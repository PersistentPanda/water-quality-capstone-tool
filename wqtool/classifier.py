"""FR-3, FR-4, FR-6 classifier. Pure functions; reads nothing and stores nothing."""
from __future__ import annotations

from dataclasses import dataclass

from wqtool.rule_loader import RuleSet, Threshold
from wqtool.validation import MEASUREMENTS, TestEntry

GREEN, YELLOW, RED, NOT_PROVIDED = "green", "yellow", "red", "not_provided"
STATUS_LABELS = {
    GREEN: "Within range",
    YELLOW: "Borderline",
    RED: "Outside range",
    NOT_PROVIDED: "Not provided",
}
WITHIN, ABOVE, BELOW = "within", "above", "below"
COLOR_NOTICE = (
    "Colors show how each result compares with the project's display ranges. "
    "They do not establish that water is safe to drink."
)


@dataclass(frozen=True)
class Result:
    parameter_id: str
    display_name: str
    unit: str
    value: float | None
    status: str            # green, yellow, red, or not_provided
    status_label: str      # written label that goes with the color (FR-4)
    position: str | None   # within, above, or below the reference (FR-3)
    comparison_text: str   # names the source of the comparison (FR-3)
    what_it_measures: str  # FR-6
    explanation: str       # FR-6
    reference_source: str


def _status(value: float, t: Threshold) -> str:
    if value > t.yellow_max:
        return RED
    if t.low_red_below is not None and value < t.low_red_below:
        return RED
    if value > t.green_max:
        return YELLOW
    if t.low_yellow_below is not None and value < t.low_yellow_below:
        return YELLOW
    return GREEN


def _position(value: float, t: Threshold) -> str:
    """Compare with the published reference, not with the display colors.

    Hardness has no published limit, so its top display boundary is used.
    """
    upper = t.reference_high if t.reference_high is not None else t.yellow_max
    if value > upper:
        return ABOVE
    if t.reference_low is not None and value < t.reference_low:
        return BELOW
    return WITHIN


def _number(value: float) -> str:
    return f"{value:g}"


def hardness_category(value: float, t: Threshold) -> str:
    """USGS category. 'Very hard' is used only if the rule file supplies its boundary."""
    very_hard = getattr(t, "very_high_above", None)
    if very_hard is not None and value > very_hard:
        return "very hard"
    if value > t.yellow_max:
        return "hard"
    if value > t.green_max:
        return "moderately hard"
    return "soft"


def _comparison_text(value: float, t: Threshold, position: str) -> str:
    if t.reference_low is None and t.reference_high is None:
        category = hardness_category(value, t).capitalize()
        return f"{category} by the {t.reference_source}."
    if t.reference_low is not None and t.reference_high is not None:
        span = f"range of {_number(t.reference_low)} to {_number(t.reference_high)}"
        if position == WITHIN:
            return f"Within the EPA secondary drinking water {span}."
        return f"{position.capitalize()} the EPA secondary drinking water {span}."
    if position == WITHIN:
        return "Within the EPA secondary drinking water guideline."
    limit = t.reference_high if position == ABOVE else t.reference_low
    return f"{position.capitalize()} the EPA secondary drinking water guideline of {_number(limit)} {t.unit}."


def classify(entry: TestEntry, ruleset: RuleSet) -> list[Result]:
    """Return one Result per measurement, in form order.

    A blank optional reading gets the not_provided status and no color. It is
    never treated as zero.
    """
    results = []
    for parameter_id in MEASUREMENTS:
        t = ruleset.thresholds[parameter_id]
        e = ruleset.explanations[parameter_id]
        value = getattr(entry, parameter_id)
        common = dict(
            parameter_id=parameter_id, display_name=t.display_name, unit=t.unit,
            value=value, what_it_measures=e.what_it_measures,
            reference_source=t.reference_source,
        )
        if value is None:
            results.append(Result(
                **common, status=NOT_PROVIDED, status_label=STATUS_LABELS[NOT_PROVIDED],
                position=None, comparison_text="Not provided", explanation="",
            ))
            continue
        status = _status(value, t)
        position = _position(value, t)
        explanation = {WITHIN: e.within_text, ABOVE: e.above_text, BELOW: e.below_text}[position]
        results.append(Result(
            **common, status=status, status_label=STATUS_LABELS[status], position=position,
            comparison_text=_comparison_text(value, t, position), explanation=explanation,
        ))
    return results
