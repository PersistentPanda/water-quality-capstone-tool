"""Load and validate the read-only rule files (design Section 2.6).

Conditions are parsed into data, never evaluated as Python. No user data is
accepted, persisted, or cached by this module.
"""
from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path


LOAD_ERROR_MESSAGE = (
    "The reference and recommendation rules could not be loaded. "
    "Please try again later."
)
MEASUREMENT_IDS = frozenset({"hardness", "iron", "ph", "tds", "manganese"})
NUMERIC_COLUMNS = (
    "reference_low", "reference_high", "green_max", "yellow_max",
    "low_yellow_below", "low_red_below",
)
TEXT_COLUMNS = ("what_it_measures", "within_text", "above_text", "below_text")
PARAMETER_COLUMNS = (
    "parameter_id", "display_name", "unit", "required", "reference_source",
    *NUMERIC_COLUMNS, *TEXT_COLUMNS,
)
RULE_COLUMNS = (
    "rule_id", "parameter_id", "condition", "suggestion_text", "reason_text",
)
_COMPARISON = re.compile(
    r"value\s*(<=|>|<)\s*(" + "|".join(NUMERIC_COLUMNS) + r")"
)


class RuleLoadError(ValueError):
    """Configuration failure. Display str(error); detail is for developers."""

    def __init__(self, detail: str):
        super().__init__(LOAD_ERROR_MESSAGE)
        self.detail = detail


@dataclass(frozen=True)
class Threshold:
    parameter_id: str
    display_name: str
    unit: str
    required: bool
    reference_source: str
    reference_low: float | None
    reference_high: float | None
    green_max: float
    yellow_max: float
    low_yellow_below: float | None
    low_red_below: float | None


@dataclass(frozen=True)
class Explanation:
    what_it_measures: str
    within_text: str
    above_text: str
    below_text: str


@dataclass(frozen=True)
class Comparison:
    operator: str
    boundary: str


@dataclass(frozen=True)
class Rule:
    rule_id: str
    parameter_id: str
    condition: str
    suggestion_text: str
    reason_text: str
    # numeric, water_source, or all_green. Numeric comparisons are ANDed.
    condition_kind: str
    comparisons: tuple[Comparison, ...] = ()
    source_value: str | None = None


@dataclass(frozen=True)
class RuleSet:
    thresholds: dict[str, Threshold]
    rules: tuple[Rule, ...]
    explanations: dict[str, Explanation]


def _rows(path: Path, required_columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if not header:
            raise RuleLoadError(f"{path.name}: missing header")
        header = [name.strip() for name in header]
        if len(header) != len(set(header)) or "" in header:
            raise RuleLoadError(f"{path.name}: duplicate or blank column name")
        if not set(required_columns).issubset(header):
            raise RuleLoadError(f"{path.name}: missing required columns")
        rows = []
        for values in reader:
            if not values or all(not value.strip() for value in values):
                continue
            if len(values) != len(header):
                raise RuleLoadError(f"{path.name}, line {reader.line_num}: wrong column count")
            rows.append(dict(zip(header, (value.strip() for value in values))))
        if not rows:
            raise RuleLoadError(f"{path.name}: no data rows")
        return rows


def _number(text: str, context: str, *, required: bool = False) -> float | None:
    if not text:
        if required:
            raise RuleLoadError(f"{context}: missing numeric value")
        return None
    try:
        number = float(text)
    except ValueError as error:
        raise RuleLoadError(f"{context}: invalid numeric value") from error
    if not math.isfinite(number):
        raise RuleLoadError(f"{context}: numeric value must be finite")
    # Reject nonzero numbers too small to represent, rather than turning them
    # silently into zero. Decimal is only used for this representation check.
    if number == 0:
        from decimal import Decimal
        if Decimal(text) != 0:
            raise RuleLoadError(f"{context}: numeric value underflows")
    return number


def _check_threshold(threshold: Threshold) -> None:
    t = threshold
    numbers = [getattr(t, name) for name in NUMERIC_COLUMNS]
    if any(value is not None and value < 0 for value in numbers):
        raise RuleLoadError(f"{t.parameter_id}: negative boundary")
    if t.green_max > t.yellow_max:
        raise RuleLoadError(f"{t.parameter_id}: green_max exceeds yellow_max")
    if (t.reference_low is not None and t.reference_high is not None
            and t.reference_low > t.reference_high):
        raise RuleLoadError(f"{t.parameter_id}: reference range is reversed")
    low_values = (t.low_red_below, t.low_yellow_below)
    if (low_values[0] is None) != (low_values[1] is None):
        raise RuleLoadError(f"{t.parameter_id}: low-side boundaries must be supplied together")
    if low_values[0] is not None:
        if not t.low_red_below <= t.low_yellow_below <= t.green_max:
            raise RuleLoadError(f"{t.parameter_id}: low-side boundaries are out of order")
    if t.parameter_id == "ph":
        if any(value is None for value in (t.reference_low, t.reference_high, *low_values)):
            raise RuleLoadError("ph: reference and low-side boundaries are required")
        if any(value is not None and value > 14 for value in numbers):
            raise RuleLoadError("ph: boundary exceeds 14")


def _parse_rule(row: dict[str, str], thresholds: dict[str, Threshold]) -> Rule:
    if any(not row[name] for name in RULE_COLUMNS):
        raise RuleLoadError("recommendations.csv: blank required value")
    parameter_id, condition = row["parameter_id"], row["condition"]
    common = {name: row[name] for name in RULE_COLUMNS}
    if parameter_id == "water_source" and condition == "water_source == Private well":
        return Rule(**common, condition_kind="water_source", source_value="Private well")
    if parameter_id == "all" and condition == "all_green":
        return Rule(**common, condition_kind="all_green")
    if parameter_id not in thresholds:
        raise RuleLoadError(f"{row['rule_id']}: unknown parameter or mismatched special condition")
    comparisons = []
    for part in re.split(r"\s+AND\s+", condition):
        match = _COMPARISON.fullmatch(part.strip())
        if match is None:
            raise RuleLoadError(f"{row['rule_id']}: unsupported condition syntax")
        operator, boundary = match.groups()
        if getattr(thresholds[parameter_id], boundary) is None:
            raise RuleLoadError(f"{row['rule_id']}: referenced boundary {boundary} is blank")
        comparisons.append(Comparison(operator, boundary))
    return Rule(**common, condition_kind="numeric", comparisons=tuple(comparisons))


def load_rules(
    parameters_path: str | Path,
    recommendations_path: str | Path,
) -> RuleSet:
    """Return a complete validated RuleSet, or raise RuleLoadError.

    Required columns must exist; extra columns are allowed but are not interpreted.
    This version supports the five measurements in TestEntry and the two agreed
    special conditions. File order is preserved. There is no partial return and
    no fallback to older or default rules when either file is invalid.
    """
    try:
        thresholds, explanations = {}, {}
        for row in _rows(Path(parameters_path), PARAMETER_COLUMNS):
            parameter_id = row["parameter_id"]
            if parameter_id not in MEASUREMENT_IDS or parameter_id in thresholds:
                raise RuleLoadError("parameters.csv: unknown or duplicate parameter_id")
            for name in ("display_name", "unit", "reference_source", *TEXT_COLUMNS[:3]):
                if not row[name]:
                    raise RuleLoadError(f"{parameter_id}: {name} is blank")
            if row["required"] not in {"true", "false"}:
                raise RuleLoadError(f"{parameter_id}: required must be true or false")
            numbers = {
                name: _number(row[name], f"{parameter_id}.{name}",
                              required=name in {"green_max", "yellow_max"})
                for name in NUMERIC_COLUMNS
            }
            threshold = Threshold(
                parameter_id=parameter_id, display_name=row["display_name"],
                unit=row["unit"], required=row["required"] == "true",
                reference_source=row["reference_source"], **numbers,
            )
            _check_threshold(threshold)
            if threshold.low_red_below is not None and not row["below_text"]:
                raise RuleLoadError(f"{parameter_id}: below_text is needed for low-side results")
            thresholds[parameter_id] = threshold
            explanations[parameter_id] = Explanation(**{name: row[name] for name in TEXT_COLUMNS})
        if set(thresholds) != MEASUREMENT_IDS:
            raise RuleLoadError("parameters.csv: one or more measurement rows are missing")
        rules, seen = [], set()
        for row in _rows(Path(recommendations_path), RULE_COLUMNS):
            if row["rule_id"] in seen:
                raise RuleLoadError("recommendations.csv: duplicate rule_id")
            rule = _parse_rule(row, thresholds)
            seen.add(rule.rule_id)
            rules.append(rule)
        return RuleSet(thresholds, tuple(rules), explanations)
    except RuleLoadError:
        raise
    except (OSError, UnicodeError, csv.Error, ValueError, OverflowError) as error:
        raise RuleLoadError(f"Unable to read rule configuration: {type(error).__name__}") from error
