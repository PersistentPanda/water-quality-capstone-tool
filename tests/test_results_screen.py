"""Results screen, print summary, and warning. IDs refer to docs/test_cases_v1.md."""
from html import escape
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from wqtool import report
from wqtool.classifier import COLOR_NOTICE
from wqtool.recommender import assess
from wqtool.rule_loader import load_rules
from wqtool.validation import TestEntry as Entry

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app.py")
FR8 = ("This tool does not test for lead, arsenic, nitrates, bacteria, or PFAS and cannot "
       "confirm that water is safe to drink. Use a certified laboratory to test for these "
       "contaminants.")
ALL_GREEN = dict(hardness=2.9, iron=0.1, ph=7.5, tds=300.0, manganese=None,
                 household_size=1, water_source="Public supply")
ALL_RED = dict(hardness=12.0, iron=0.4, ph=6.0, tds=600.0, manganese=0.06,
               household_size=4, water_source="Private well")


@pytest.fixture(scope="module")
def ruleset():
    return load_rules(ROOT / "data/parameters.csv", ROOT / "data/recommendations.csv")


def summary(ruleset, values):
    entry = Entry(**values)
    return report.summary_body_html(entry, assess(entry, ruleset))


def test_warning_text_is_exact():
    assert report.LAB_WARNING == FR8


@pytest.mark.parametrize("values", [ALL_GREEN, ALL_RED])
def test_t27_summary_always_carries_the_warning(ruleset, values):
    assert FR8 in summary(ruleset, values)


def test_t26_summary_matches_the_results(ruleset):
    entry = Entry(**ALL_RED)
    assessment = assess(entry, ruleset)
    html = report.summary_body_html(entry, assessment)
    assert "Household: 4 people. Water source: Private well." in html
    for result in assessment.results:
        assert result.display_name in html
        assert f"{result.status.capitalize()}: {result.status_label}" in html
        assert escape(result.explanation) in html
    for suggestion in assessment.suggestions:
        assert escape(suggestion.suggestion_text) in html and escape(suggestion.reason_text) in html
    assert "USGS hardness classification" in html and "EPA secondary standard" in html
    assert escape(COLOR_NOTICE) in html


def test_blank_manganese_prints_not_provided_without_a_color(ruleset):
    entry = Entry(**ALL_GREEN)
    manganese = [r for r in assess(entry, ruleset).results if r.parameter_id == "manganese"][0]
    assert report.status_chip(manganese) == "Not provided"
    assert report.format_value(manganese) == "Not provided"


def test_values_show_units(ruleset):
    results = {r.parameter_id: r for r in assess(Entry(**ALL_RED), ruleset).results}
    assert report.format_value(results["hardness"]) == "12 gpg"
    assert report.format_value(results["iron"]) == "0.4 mg/L"
    assert report.format_value(results["ph"]) == "6"


def test_print_component_has_one_button_and_hides_summary_on_screen(ruleset):
    entry = Entry(**ALL_RED)
    html = report.print_component_html(entry, assess(entry, ruleset))
    assert html.count("<button") == 1 and "Print summary" in html
    assert 'onclick="window.print()"' in html and "#summary { display: none; }" in html


def test_rule_text_is_escaped(ruleset):
    entry = Entry(**ALL_RED)
    assessment = assess(entry, ruleset)
    risky = type(assessment.results[0])(**{**assessment.results[0].__dict__, "explanation": "<script>x</script>"})
    assert "<script>" not in report.results_table_html((risky,))


def fill(app, values, source):
    for widget, value in zip(app.text_input, values):
        widget.input(value)
    app.selectbox[0].select(source)
    app.button[0].click().run()
    return app


def page_text(app):
    return "\n".join(str(m.value) for m in [*app.markdown, *app.caption, *app.warning])


def test_results_screen_shows_statuses_suggestions_and_warning():
    app = fill(AppTest.from_file(APP).run(), ["8.8", "0.2", "7.2", "300", "", "4"], "Private well")
    assert not app.exception
    text = page_text(app)
    assert "Red: Outside range" in text and "Green: Within range" in text
    assert "Consider water softening for hardness and scale concerns." in text
    assert "Not provided" in text
    assert COLOR_NOTICE in text                      # T-20
    assert FR8 in text                               # T-27
    assert "Household: 4 people. Water source: Private well." in text


def test_no_results_when_entry_is_invalid():
    app = fill(AppTest.from_file(APP).run(), ["8.8", "0.2", "15", "300", "", "4"], "Private well")
    assert app.error and "Your results" not in [h.value for h in app.subheader]
    assert FR8 in page_text(app)


def test_t43_missing_rule_file_stops_before_the_form(tmp_path, monkeypatch):
    import streamlit as st
    st.cache_resource.clear()
    app_copy = tmp_path / "app.py"
    app_copy.write_text((ROOT / "app.py").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.syspath_prepend(str(ROOT))
    app = AppTest.from_file(str(app_copy)).run()
    assert len(app.error) == 1
    assert app.error[0].value == "The reference and recommendation rules could not be loaded. Please try again later."
    assert not app.text_input
    st.cache_resource.clear()
