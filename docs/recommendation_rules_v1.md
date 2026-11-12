# Recommendation rules v1

Owner: Hector, with treatment wording reviewed by Daniel (water treatment lab). Scope: the 14-row CSV for FR-5, not the recommender implementation.
No manufacturer, dosage, equipment size, or health-safety conclusion is generated.
Household size and water source remain available to the later recommender but these draft rules do not use them to invent equipment-sizing thresholds.

## Proposed condition contract

The five columns follow Section 2.4 of the design document. `parameter_id` matches
Daniel's `data/parameters.csv` exactly (`ph` and `tds` are lower case).
For each row, `value` means that parameter's submitted numeric reading.
The other names resolve to numeric fields in that parameter's parameters.csv row.
Allowed operators in this draft: `>`, `>=`, `<`, `<=`, joined with `AND`, for numeric rows.
Two non-numeric conditions are also supported: `water_source == Private well` (string equality on the
submitted water source) and `all_green` (true when every entered measurement is at or below its
`green_max` and, for pH, at or above `low_yellow_below`; a blank optional manganese is ignored).
The future loader must validate this restricted grammar; do not use Python eval.
A referenced blank or nonnumeric boundary is a configuration error and stops assessment.
An absent optional manganese reading skips its rules entirely; it must never become zero.
Evaluate all matching rows in file order and retain rule_id and parameter_id for traceability.
These conditions are a proposed interface, since the README does not yet define recommendation condition syntax.

Hardness is in grains per gallon (gpg). R01 includes 8.8 gpg and excludes 2.9 gpg (the FR-5 acceptance
example restated in gpg). R02 includes 7 and excludes 3.5. R03 includes iron above 0.3, while R04 includes
0.3 and excludes 0.24. pH 6.5 and 8.5 do not trigger R05/R06; they fall in the yellow band and trigger R13 and R14.
R13 includes pH 6.5 and 6.9 and excludes 7.0. R14 includes 8.1 and 8.5 and excludes 8.0. R07/R09 exclude
values exactly equal to the respective secondary upper limits. R08/R10 include
those upper limits but exclude values equal to green_max. Team display colors
and published comparison limits remain separate.

## Review notes (Nov 10, Daniel)

Condition format approved. Treatment wording for R03, R05, R06, R07, and R09 was revised to name the
standard treatment category in plain words (iron filter, acid neutralizer, point-of-use reverse osmosis,
combined iron/manganese filtration) while still directing the user to further testing before any purchase.
These categories are the corrective technologies listed on the EPA secondary standards page; no sizing,
brand, dosage, or health claim is made. R11 (private well annual lab test) and R12 (all-green, no treatment
indicated) were added so a well owner always receives the testing reminder and a user with clean results
receives a clear answer rather than the "cannot provide a suggestion" fallback.

## Additions (Nov 12)

R13 and R14 give yellow pH a monitoring suggestion, matching the yellow-band rules the other four
measurements already have. Before this, an entry that was all green except a yellow pH matched no rule.
R13 needed the `>=` operator so that pH exactly 6.5 is included (R05 only covers values below 6.5).

`parameters.csv` has a new column, `very_high_above`, set to 10.5 for hardness and blank for the others.
It is a description boundary, not a color boundary: hardness above 10.5 gpg is described as "very hard"
(USGS: above 180 mg/L). Colors are unchanged, so hardness above 7 gpg is still red and still triggers R01.
This gives FR-3 its four categories: soft, moderately hard, hard, very hard.

## Review sources

EPA secondary standards and treatment overview:
https://www.epa.gov/sdwa/secondary-drinking-water-standards-guidance-nuisance-chemicals

USGS hardness classification:
https://www.usgs.gov/water-science-school/science/hardness-water

The monitoring suggestions and condition structure are proposed team rules, not EPA-issued recommendations.
Secondary guideline comparisons do not determine drinking-water safety. Keep the exact FR-8 laboratory warning on all results and reports, independently of whether any rule matches.

## Pull request description

Adds twelve recommendation rules using parameter IDs and symbolic boundaries from parameters.csv. Includes the proposed supported condition grammar, boundary behavior, and review sources. Treatment wording reviewed by Daniel; condition contract approved. Ready for the recommender integration.
