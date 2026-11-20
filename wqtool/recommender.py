"""FR-5 recommender. Applies the loaded rules in file order. No eval, no stored state."""
from __future__ import annotations

import operator
from dataclasses import dataclass

from wqtool.classifier import GREEN, NOT_PROVIDED, Result, classify
from wqtool.rule_loader import Rule, RuleSet
from wqtool.validation import TestEntry

NO_SUGGESTION_MESSAGE = (
    "The tool cannot provide a suggestion for these entries. "
    "Discuss your results with a water treatment professional."
)
_OPERATORS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}


@dataclass(frozen=True)
class Suggestion:
    rule_id: str
    parameter_id: str      # the result that caused the suggestion
    suggestion_text: str
    reason_text: str


@dataclass(frozen=True)
class Assessment:
    results: tuple[Result, ...]
    suggestions: tuple[Suggestion, ...]


def _matches(rule: Rule, entry: TestEntry, results: list[Result], ruleset: RuleSet) -> bool:
    if rule.condition_kind == "water_source":
        return entry.water_source == rule.source_value
    if rule.condition_kind == "all_green":
        entered = [r for r in results if r.status != NOT_PROVIDED]
        return bool(entered) and all(r.status == GREEN for r in entered)
    if rule.condition_kind != "numeric":
        raise ValueError(f"{rule.rule_id}: unknown condition kind {rule.condition_kind}")
    value = getattr(entry, rule.parameter_id)
    if value is None:           # blank optional reading: skip its rules
        return False
    threshold = ruleset.thresholds[rule.parameter_id]
    return all(
        _OPERATORS[c.operator](value, getattr(threshold, c.boundary))
        for c in rule.comparisons
    )


def recommend(entry: TestEntry, results: list[Result], ruleset: RuleSet) -> list[Suggestion]:
    """Return every matching rule's suggestion, in rule-file order."""
    return [
        Suggestion(rule.rule_id, rule.parameter_id, rule.suggestion_text, rule.reason_text)
        for rule in ruleset.rules
        if _matches(rule, entry, results, ruleset)
    ]


def assess(entry: TestEntry, ruleset: RuleSet) -> Assessment:
    """Classify a valid entry, then apply the rules. Same input, same output."""
    results = classify(entry, ruleset)
    return Assessment(tuple(results), tuple(recommend(entry, results, ruleset)))
