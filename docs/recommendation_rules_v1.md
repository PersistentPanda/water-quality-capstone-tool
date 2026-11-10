# Recommendation rules v1 — review draft

Owner: Hector. Scope: the 10-row CSV for FR-5, not the recommender implementation.
Daniel should review the treatment language and approve the condition format before integration.
No manufacturer, dosage, equipment size, or health-safety conclusion is generated.
Household size and water source remain available to the later recommender but these draft rules do not use them to invent equipment-sizing thresholds.

## Proposed condition contract

The five columns follow Section 2.4 of the design document. `parameter_id` matches
Daniel's `data/parameters.csv` exactly (`ph` and `tds` are lower case).
For each row, `value` means that parameter's submitted numeric reading.
The other names resolve to numeric fields in that parameter's parameters.csv row.
Allowed operators in this draft: `>`, `<`, `<=`, joined with `AND`.
The future loader must validate this restricted grammar; do not use Python eval.
A referenced blank or nonnumeric boundary is a configuration error and stops assessment.
An absent optional manganese reading skips its rules entirely; it must never become zero.
Evaluate all matching rows in file order and retain rule_id and parameter_id for traceability.
These conditions are a proposed interface, since the README does not yet define recommendation condition syntax.

R01 includes hardness 150 but excludes 50, matching the FR-5 acceptance example.
R02 includes 120 and excludes 60. R03 includes iron above 0.3, while R04 includes
0.3 and excludes 0.24. pH 6.5 and 8.5 do not trigger R05/R06. R07/R09 exclude
values exactly equal to the respective secondary upper limits. R08/R10 include
those upper limits but exclude values equal to green_max. Team display colors
and published comparison limits remain separate.

## Review sources

EPA secondary standards and treatment overview:
https://www.epa.gov/sdwa/secondary-drinking-water-standards-guidance-nuisance-chemicals

USGS hardness classification:
https://www.usgs.gov/water-science-school/science/hardness-water

The monitoring suggestions and condition structure are proposed team rules, not EPA-issued recommendations.
Secondary guideline comparisons do not determine drinking-water safety. Keep the exact FR-8 laboratory warning on all results and reports, independently of whether any rule matches.

## Suggested pull request description

Adds ten draft recommendation rules using parameter IDs and symbolic boundaries from parameters.csv. Includes the proposed supported condition grammar, boundary behavior, and review sources. Treatment wording and the condition contract need Daniel's review before the recommender is connected.
