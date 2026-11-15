"""Classifier and recommender tests. IDs in comments refer to docs/test_cases_v1.md."""
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from wqtool.classifier import COLOR_NOTICE, classify, hardness_category
from wqtool.recommender import NO_SUGGESTION_MESSAGE, assess, recommend
from wqtool.rule_loader import Comparison, Rule, load_rules
from wqtool.validation import TestEntry as Entry

DATA = Path(__file__).resolve().parents[1] / "data"
SOFTENING = "Consider water softening for hardness and scale concerns."


@pytest.fixture(scope="module")
def ruleset():
    return load_rules(DATA / "parameters.csv", DATA / "recommendations.csv")


def entry(**changes):
    """Standard entry from the test case list."""
    base = dict(hardness=8.8, iron=0.2, ph=7.2, tds=300.0, manganese=0.02,
                household_size=4, water_source="Private well")
    return Entry(**{**base, **changes})


def all_green(**changes):
    return entry(**{**dict(hardness=2.9, iron=0.1, ph=7.5, tds=300.0, manganese=None,
                           water_source="Public supply"), **changes})


def status(ruleset, parameter_id, **changes):
    return {r.parameter_id: r for r in classify(entry(**changes), ruleset)}[parameter_id]


def rule_ids(ruleset, test_entry):
    return [s.rule_id for s in assess(test_entry, ruleset).suggestions]


# FR-3

def test_t12_t13_tds_comparison_text(ruleset):
    assert status(ruleset, "tds", tds=300).comparison_text == \
        "Within the EPA secondary drinking water guideline."
    assert status(ruleset, "tds", tds=600).comparison_text == \
        "Above the EPA secondary drinking water guideline of 500 mg/L."


@pytest.mark.parametrize("value,category", [(2.9, "Soft"), (5, "Moderately hard"), (8.8, "Hard")])
def test_t14_hardness_category_names_source(ruleset, value, category):
    result = status(ruleset, "hardness", hardness=value)
    assert result.comparison_text == f"{category} by the USGS hardness classification."


def test_ph_comparison_text(ruleset):
    assert status(ruleset, "ph", ph=7.2).comparison_text == \
        "Within the EPA secondary drinking water range of 6.5 to 8.5."
    assert status(ruleset, "ph", ph=6.0).comparison_text.startswith("Below ")
    assert status(ruleset, "ph", ph=9.0).comparison_text.startswith("Above ")


def test_very_hard_used_only_when_boundary_is_supplied(ruleset):
    t = ruleset.thresholds["hardness"]
    assert hardness_category(12, t) == "hard"

    class WithVeryHard:
        green_max, yellow_max, very_high_above = t.green_max, t.yellow_max, 10.5

    assert hardness_category(12, WithVeryHard) == "very hard"
    assert hardness_category(10.5, WithVeryHard) == "hard"


# FR-4

@pytest.mark.parametrize("parameter_id,cases", [
    ("iron", [(0.10, "green"), (0.24, "green"), (0.27, "yellow"), (0.30, "yellow"), (0.40, "red")]),   # T-15
    ("ph", [(6.0, "red"), (6.5, "yellow"), (6.8, "yellow"), (7.0, "green"), (7.5, "green"),
            (8.0, "green"), (8.3, "yellow"), (8.5, "yellow"), (9.0, "red")]),                            # T-16
    ("tds", [(300, "green"), (400, "green"), (450, "yellow"), (500, "yellow"), (600, "red")]),          # T-17
    ("manganese", [(0.02, "green"), (0.045, "yellow"), (0.06, "red")]),                                  # T-18
    ("hardness", [(2.9, "green"), (3.5, "green"), (5, "yellow"), (7, "yellow"), (8.8, "red")]),         # T-19
])
def test_colors(ruleset, parameter_id, cases):
    for value, expected in cases:
        result = status(ruleset, parameter_id, **{parameter_id: value})
        assert result.status == expected, (parameter_id, value)
        assert result.status_label


def test_t18_blank_manganese_has_no_color(ruleset):
    result = status(ruleset, "manganese", manganese=None)
    assert (result.status, result.status_label, result.value) == ("not_provided", "Not provided", None)


def test_zero_is_an_entered_reading(ruleset):
    assert status(ruleset, "manganese", manganese=0.0).status == "green"


def test_t20_color_notice_makes_no_safety_claim():
    assert "do not establish" in COLOR_NOTICE


# FR-6

def test_t24_five_explanations(ruleset):
    results = classify(entry(), ruleset)
    assert [r.parameter_id for r in results] == ["hardness", "iron", "ph", "tds", "manganese"]
    assert all(r.what_it_measures and r.explanation for r in results)


def test_t25_iron_above_explanation(ruleset):
    text = status(ruleset, "iron", iron=0.4).explanation
    assert "above the EPA secondary guideline" in text and "staining" in text


def test_low_ph_uses_below_text(ruleset):
    assert "below the EPA secondary range" in status(ruleset, "ph", ph=6.0).explanation


# FR-5

def test_t21_t22_softening_suggestion(ruleset):
    hard = assess(entry(hardness=8.8, iron=0.1, ph=7.2, tds=200.0), ruleset)
    softening = [s for s in hard.suggestions if s.suggestion_text == SOFTENING]
    assert len(softening) == 1 and softening[0].parameter_id == "hardness"
    assert "Hardness" in softening[0].reason_text
    soft = assess(entry(hardness=2.9, iron=0.1, ph=7.2, tds=200.0), ruleset)
    assert SOFTENING not in [s.suggestion_text for s in soft.suggestions]


def test_t23_same_input_same_output(ruleset):
    assert assess(entry(), ruleset) == assess(entry(), ruleset)


@pytest.mark.parametrize("rule_id,field,triggers,does_not", [
    ("R01", "hardness", [7.1], [7.0]),                 # T-30
    ("R02", "hardness", [3.6, 7.0], [3.5, 7.1]),       # T-31
    ("R03", "iron", [0.31], [0.30]),                   # T-32
    ("R04", "iron", [0.25, 0.30], [0.24, 0.31]),       # T-33
    ("R05", "ph", [6.4], [6.5]),                       # T-34
    ("R06", "ph", [8.6], [8.5]),                       # T-35
    ("R07", "tds", [501], [500]),                      # T-36
    ("R08", "tds", [401, 500], [400, 501]),            # T-37
    ("R09", "manganese", [0.051], [0.05]),             # T-38
    ("R10", "manganese", [0.041, 0.05], [0.04, 0.051]),  # T-39
])
def test_rule_boundaries(ruleset, rule_id, field, triggers, does_not):
    for value in triggers:
        assert rule_id in rule_ids(ruleset, all_green(**{field: value})), value
    for value in does_not:
        assert rule_id not in rule_ids(ruleset, all_green(**{field: value})), value


def test_t40_blank_manganese_triggers_no_manganese_rule(ruleset):
    ids = rule_ids(ruleset, all_green(manganese=None))
    assert "R09" not in ids and "R10" not in ids


def test_t41_private_well_rule(ruleset):
    assert "R11" in rule_ids(ruleset, entry(water_source="Private well"))
    assert "R11" not in rule_ids(ruleset, entry(water_source="Public supply"))


def test_t42_all_green_rule(ruleset):
    assert rule_ids(ruleset, all_green()) == ["R12"]
    assert "R12" not in rule_ids(ruleset, all_green(iron=0.27))


@pytest.mark.parametrize("ph", [6.8, 8.3, 6.0, 9.0])
def test_t42b_all_green_never_with_yellow_or_red_ph(ruleset, ph):
    assert "R12" not in rule_ids(ruleset, all_green(ph=ph))


def test_t42c_private_well_and_all_green_together(ruleset):
    assert rule_ids(ruleset, all_green(water_source="Private well")) == ["R11", "R12"]
    assert rule_ids(ruleset, all_green(water_source="Public supply")) == ["R12"]


def test_suggestions_follow_file_order(ruleset):
    ids = rule_ids(ruleset, entry(hardness=8.8, iron=0.4, ph=6.0, tds=600.0, manganese=0.06))
    assert ids == ["R01", "R03", "R05", "R07", "R09", "R11"]


def test_fallback_message_exists_for_no_match():
    assert "cannot provide a suggestion" in NO_SUGGESTION_MESSAGE


def test_greater_or_equal_operator_is_supported(ruleset):
    """The yellow-pH rule proposed in PR #7 uses >=."""
    rule = Rule("RX", "ph", "value < low_yellow_below AND value >= reference_low", "s", "r",
                condition_kind="numeric",
                comparisons=(Comparison("<", "low_yellow_below"), Comparison(">=", "reference_low")))
    extended = replace(ruleset, rules=(rule,))
    for ph, expected in [(6.5, ["RX"]), (6.9, ["RX"]), (6.4, []), (7.0, [])]:
        test_entry = all_green(ph=ph)
        got = [s.rule_id for s in recommend(test_entry, classify(test_entry, extended), extended)]
        assert got == expected, ph


# NFR-6

def test_t55_threshold_change_needs_no_code_edit(tmp_path):
    for name in ("parameters.csv", "recommendations.csv"):
        shutil.copy(DATA / name, tmp_path / name)
    path = tmp_path / "parameters.csv"
    before = load_rules(path, tmp_path / "recommendations.csv")
    assert status(before, "iron", iron=0.40).status == "red"
    text = path.read_text(encoding="utf-8")
    assert ",0.24,0.30," in text
    path.write_text(text.replace(",0.24,0.30,", ",0.24,0.50,"), encoding="utf-8")
    after = load_rules(path, tmp_path / "recommendations.csv")
    assert status(after, "iron", iron=0.40).status == "yellow"
