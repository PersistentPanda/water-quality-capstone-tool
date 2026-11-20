"""Build data/county_summary.csv for the Power BI dashboard (FR-9).

One row per county and measurement, with the median, the number of samples,
and a full location name that a map can place without guessing.

    python tools/build_county_summary.py
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wqtool.classifier import STATUS_LABELS, _status  # noqa: E402
from wqtool.rule_loader import load_rules  # noqa: E402

STATE_NAMES = {"MD": "Maryland"}
FEW_SAMPLES = 5
COLUMNS = [
    "area_id", "county", "state", "location", "parameter_id", "measurement", "unit",
    "median_value", "sample_count", "not_detected_count", "few_samples",
    "status", "status_label", "first_sample_date", "last_sample_date", "data_source",
]


def build(rows: list[dict[str, str]], ruleset) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["area_id"], row["parameter_id"])].append(row)
    out = []
    for (area_id, parameter_id), group in sorted(groups.items()):
        first = group[0]
        values = [float(r["value"]) for r in group if r["value"] != ""]
        if not values:      # every sample was below detection: no median to show
            continue
        threshold = ruleset.thresholds[parameter_id]
        median = round(statistics.median(values), 4)
        status = _status(median, threshold)
        county = f"{first['area_name']} County"
        dates = sorted(r["sample_date"] for r in group)
        out.append({
            "area_id": area_id,
            "county": county,
            "state": first["state"],
            "location": f"{county}, {STATE_NAMES[first['state']]}, USA",
            "parameter_id": parameter_id,
            "measurement": threshold.display_name,
            "unit": first["unit"],
            "median_value": f"{median:g}",
            "sample_count": len(values),
            "not_detected_count": len(group) - len(values),
            "few_samples": "yes" if len(values) < FEW_SAMPLES else "no",
            "status": status,
            "status_label": STATUS_LABELS[status],
            "first_sample_date": dates[0],
            "last_sample_date": dates[-1],
            "data_source": first["data_source"],
        })
    return out


def main() -> None:
    with open(ROOT / "data/public_water_data.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    ruleset = load_rules(ROOT / "data/parameters.csv", ROOT / "data/recommendations.csv")
    summary = build(rows, ruleset)
    with open(ROOT / "data/county_summary.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(summary)
    print(f"Wrote {len(summary)} rows for {len({r['area_id'] for r in summary})} counties.")


if __name__ == "__main__":
    main()
