"""County summary for the dashboard (FR-9). IDs refer to docs/test_cases_v1.md."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_county_summary as summary  # noqa: E402
from wqtool.rule_loader import load_rules  # noqa: E402


def load(name):
    with open(ROOT / "data" / name, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def built():
    ruleset = load_rules(ROOT / "data/parameters.csv", ROOT / "data/recommendations.csv")
    return summary.build(load("public_water_data.csv"), ruleset)


def test_committed_file_matches_the_script():
    expected = [{k: str(v) for k, v in row.items()} for row in built()]
    assert load("county_summary.csv") == expected


def test_t28b_garrett_medians_and_counts():
    rows = {r["parameter_id"]: r for r in built() if r["county"] == "Garrett County"}
    assert (rows["hardness"]["median_value"], rows["hardness"]["sample_count"]) == ("4.1", 113)
    assert (rows["iron"]["median_value"], rows["iron"]["sample_count"]) == ("0.162", 97)
    assert (rows["ph"]["median_value"], rows["ph"]["sample_count"]) == ("7.8", 125)
    assert (rows["tds"]["median_value"], rows["tds"]["sample_count"]) == ("152.5", 110)
    assert rows["iron"]["not_detected_count"] == 16   # left out of the median, not counted as 0


def test_one_row_per_county_and_measurement_with_full_location():
    rows = built()
    keys = [(r["area_id"], r["parameter_id"]) for r in rows]
    assert len(keys) == len(set(keys))
    assert all(r["location"].endswith(" County, Maryland, USA") for r in rows)
    assert "Washington County, Maryland, USA" in {r["location"] for r in rows}


def test_few_samples_flag():
    for r in built():
        assert r["few_samples"] == ("yes" if r["sample_count"] < 5 else "no")
