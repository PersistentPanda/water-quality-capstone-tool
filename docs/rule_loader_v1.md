# Rule loader v1 — Hector

Implements `load_rules(parameters_path, recommendations_path) -> RuleSet` from design Section 2.6. This build uses the uploaded parameters.csv v1.1 and the twelve approved rules as regression fixtures. It does not change their treatment wording, add yellow-pH rules, or add the proposed very-hard boundary.

## Install and check

Copy these folders into the repository root, merging with the existing folders:

- `wqtool/rule_loader.py`
- `tests/test_rule_loader.py`
- `tests/fixtures/rule_loader/parameters.csv`
- `tests/fixtures/rule_loader/recommendations.csv`
- `docs/rule_loader_v1.md`

Do not replace app.py, validation.py, the production data folder, or either existing folder wholesale. The fixture CSVs live inside tests and are deliberately separate from production data.

From a command prompt in the repository:

```bat
py -m pytest tests/test_rule_loader.py -q
py -m pytest tests/ -q
```

The new tests use pytest and the Python standard library; there are no new runtime dependencies. Existing tests should also be run on the user's current branch before committing.

Local verification: 66 loader tests passed with Python 3.12 and pytest 9.2.0. The full suite on the current Windows branch still needs to be run after copying these files.

## Interface for Daniel

```python
from pathlib import Path
from wqtool.rule_loader import load_rules, RuleLoadError

root = Path(__file__).resolve().parent  # when called from app.py
ruleset = load_rules(root / "data/parameters.csv", root / "data/recommendations.csv")
```

- `ruleset.thresholds`: dictionary keyed by parameter ID. Each Threshold has `parameter_id`, `display_name`, `unit`, `required` (a boolean), `reference_source`, and the six numeric boundary fields. Applicable boundaries are floats; intentionally absent reference values are None.
- `ruleset.explanations`: dictionary with the same IDs. Each Explanation holds `what_it_measures`, `within_text`, `above_text`, `below_text`.
- `ruleset.rules`: tuple in CSV order. Each Rule retains `rule_id`, `parameter_id`, original trimmed `condition`, `suggestion_text`, `reason_text`, plus the parsed fields below. There is no fixed limit of twelve rules.

| condition_kind | Parsed data | Recommender responsibility |
|---|---|---|
| numeric | `comparisons`: tuple of Comparison(operator, boundary) | Resolve boundary names from that rule's Threshold; AND the comparisons; skip absent optional readings. |
| water_source | `source_value`: `Private well` | Compare to entry.water_source. |
| all_green | No numeric comparisons | Match only when every entered measurement is green, including the low pH boundary; ignore missing optional manganese. |

The loader parses conditions; it does not classify user entries or generate suggestions. The recommender must evaluate all matching rules in file order, so R11 and R12 can both appear for an all-green private-well entry. No entry or results are passed to this loader.

Numeric grammar is one or more `value > boundary`, `value < boundary`, or `value <= boundary` comparisons joined by uppercase `AND`. The boundary must be one of the six numeric columns and must be populated in the referenced parameter row. Literal numeric thresholds, OR, function calls, arbitrary expressions, and other operators are rejected. The two special conditions are accepted only with their matching IDs: `water_source` and `all`. Neither eval nor exec is used.

## Failure handling and startup integration

On any supported file/configuration error, the loader raises RuleLoadError. Its public string is exactly:

> The reference and recommendation rules could not be loaded. Please try again later.

`error.detail` contains a developer-oriented diagnostic. Do not display it to homeowners. No partial RuleSet or guessed default is returned.

When wiring the results pipeline in app.py, load and retain the rule set before allowing an assessment. For example:

```python
try:
    ruleset = load_rules(root / "data/parameters.csv", root / "data/recommendations.csv")
except RuleLoadError as error:
    st.error(str(error))
    st.stop()
```

Use a suitable startup lifecycle when integrating with Streamlit reruns. This module intentionally has no hidden global cache; a new load reads current CSV contents. Keep user entries and outputs in their individual session, outside any shared rule cache. app.py is not modified in this delivery, so the current form remains an input-validation prototype until the team wires the loader/classifier/recommender together. The current form/validator still need the earlier agreed CSV metadata integration (`display_name`, `unit`, `required`).

## Checks

Checks cover both files being present and readable; headers and row widths; required columns and values; duplicate identifiers and headers; five expected measurement rows; true/false required flags; finite representable numeric fields; sensible ordered ranges; pH reference/low-side configuration; rule parameter references; populated referenced boundaries; restricted condition syntax; special condition scope; and unchanged file contents after loading. Empty files, header-only files, malformed quotes and invalid UTF-8 are rejected.

Extra CSV columns are permitted but not interpreted. A future very-hard column or new condition operator will need an explicit interface update; this loader must not silently invent its meaning. Reference limits and color boundaries are checked separately: changing iron yellow_max to 0.50 while reference_high stays 0.30 is allowed, matching T-55. Missing optional numeric reference fields stay None; an absent green_max or yellow_max is an error. Numeric fields reject NaN, infinity, overflow, nonzero underflow, and negative values.

Tests of color classification, recommendation matching (including R11/R12 together), dashboard medians and printable reports belong to the corresponding modules. The loader tests verify that these modules receive validated configuration, not that the later modules have already been implemented.
