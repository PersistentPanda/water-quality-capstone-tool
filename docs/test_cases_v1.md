# Test case list v1

Starting point for the Unit 6 test plan document. One or more test cases per requirement
in the requirements document (FR-1 to FR-9, NFR-1 to NFR-6), plus boundary cases for the
twelve recommendation rules and the rule loader checks from design document Section 2.6.

Conventions:

- Hardness is in grains per gallon (gpg). The requirements document wrote its hardness
  examples in mg/L (150 and 50). The same examples here are 8.8 gpg and 2.9 gpg.
- Iron, TDS, and manganese are in mg/L. pH has no unit.
- "Standard entry" means: hardness 8.8, iron 0.2, pH 7.2, TDS 300, manganese 0.02,
  household size 4, water source Private well.
- Type: A = automated (pytest), M = manual check in the browser.
- Status: Done = an automated test in `tests/` already checks this. Partly = a test checks the
  behavior but not the exact message. Open = the feature is not built yet, or the check has not
  been run. Every expected result marked Done or Partly was confirmed against the current code.

## Functional requirements

| ID | Req | Input | Expected result | Type | Status |
|---|---|---|---|---|---|
| T-01 | FR-1 | Standard entry with pH 15 | Blocked. Message: "Enter pH between 0 and 14." Other fields keep their values. | A | Done (`test_ph_boundaries`, `test_form_preserves_errors_and_resets_session`) |
| T-02 | FR-1 | Standard entry with pH 0, then pH 14 | Both accepted. | A | Done (`test_ph_boundaries`) |
| T-03 | FR-1 | Standard entry with iron left blank | Blocked. Message: "Please enter the iron result before continuing." | A | Partly (`test_required` checks it is blocked; the message text is not asserted yet) |
| T-04 | FR-1 | Standard entry with iron -0.01 | Blocked. Message: "Enter an iron value of zero or greater." | A | Partly (`test_negative_concentrations` checks it is blocked; message text not asserted) |
| T-05 | FR-1 | Standard entry with TDS "abc" | Blocked. Message: "Enter a number for TDS, such as 300." | A | Partly (`test_unusable_numeric` checks non-numeric iron is blocked; message text not asserted) |
| T-06 | FR-1 | Household size 0, -1, 2.5, "people" | Each blocked. Message: "Enter the number of people as a whole number of at least 1." | A | Partly (`test_bad_household` checks each is blocked; message text not asserted) |
| T-07 | FR-1 | Standard entry with manganese blank | Accepted. Manganese shows "Not provided", never 0. | A | Done (`test_optional_blank`) |
| T-08 | FR-1 | No water source selected | Blocked. Message: "Select either Private well or Public supply." | A | Partly (`test_multiple_errors_and_no_mutation` counts the message; text not asserted) |
| T-09 | FR-1 | Iron blank, pH 15, no water source | Three messages shown together. Nothing is assessed. | A | Done (`test_multiple_errors_and_no_mutation`) |
| T-10 | FR-2 | Standard entry | All seven entries appear correctly in the submitted values, with units shown on the form. | A | Done (`test_fr2_sample_round_trip`) |
| T-11 | FR-2 | Open the form | Hardness label shows gpg. Iron, TDS, manganese show mg/L. Required fields are marked. | M | Open |
| T-12 | FR-3 | Standard entry (TDS 300) | TDS comparison: "Within the EPA secondary drinking water guideline." | A | Open |
| T-13 | FR-3 | Standard entry with TDS 600 | TDS comparison: "Above the EPA secondary drinking water guideline of 500 mg/L." | A | Open |
| T-14 | FR-3 | Hardness 2.9, then 5, then 8.8 | Described as soft, moderately hard, hard (USGS). The source of the comparison is named. | A | Open |
| T-15 | FR-4 | Iron 0.10, 0.27, 0.40 | Green, yellow, red. Each color has a written label. | A | Open |
| T-16 | FR-4 | pH 6.0, 6.8, 7.5, 8.3, 9.0 | Red, yellow, green, yellow, red. | A | Open |
| T-17 | FR-4 | TDS 300, 450, 600 | Green, yellow, red. | A | Open |
| T-18 | FR-4 | Manganese 0.02, 0.045, 0.06, blank | Green, yellow, red, "Not provided" with no color. | A | Open |
| T-19 | FR-4 | Hardness 2.9, 5, 8.8 | Green, yellow, red. | A | Open |
| T-20 | FR-4 | Any results screen | The screen states that colors do not establish drinking-water safety. | M | Open |
| T-21 | FR-5 | Hardness 8.8, iron 0.1, pH 7.2, TDS 200, household 4 | Suggestion shown: "Consider water softening for hardness and scale concerns." The reason names hardness. | A | Open |
| T-22 | FR-5 | Same as T-21 with hardness 2.9 | The softening suggestion does not appear. | A | Open |
| T-23 | FR-5 | Standard entry, run twice | Same suggestions both times, in the same order. | A | Open |
| T-24 | FR-6 | All five measurements entered | Five explanations appear, one per measurement, each one or two sentences. | A | Open |
| T-25 | FR-6 | Iron 0.4 | Explanation says the result is above the EPA secondary guideline and mentions staining or metallic taste. | A | Open |
| T-26 | FR-7 | Standard entry, then select "Print summary" once | Print preview is one page. Values, statuses, explanations, suggestions, sources, and the warning match the results screen. | M | Open |
| T-27 | FR-8 | An all-green entry and an entry with at least one red | Both results screens and both printed summaries show the full laboratory warning, word for word. | A and M | Open |
| T-28 | FR-9 | Dashboard, select area A, then area B | Only the selected area's records appear. Source, units, and sample dates are shown. Hardness is in gpg. | M | Open |
| T-29 | FR-9 | An area with one measurement missing | Dashboard shows "No data" for it, not zero. | M | Open |

## Recommendation rule boundaries (FR-5)

Each row gives a value that must trigger the rule and the nearest value that must not.
All other measurements are held at green values unless stated.

| ID | Rule | Triggers at | Does not trigger at | Type | Status |
|---|---|---|---|---|---|
| T-30 | R01 hardness, hard | 7.1 gpg | 7.0 gpg (R02 instead) | A | Open |
| T-31 | R02 hardness, moderately hard | 3.6 and 7.0 gpg | 3.5 gpg | A | Open |
| T-32 | R03 iron above guideline | 0.31 | 0.30 (R04 instead) | A | Open |
| T-33 | R04 iron near guideline | 0.25 and 0.30 | 0.24 | A | Open |
| T-34 | R05 low pH | 6.4 | 6.5 | A | Open |
| T-35 | R06 high pH | 8.6 | 8.5 | A | Open |
| T-36 | R07 TDS above guideline | 501 | 500 (R08 instead) | A | Open |
| T-37 | R08 TDS near guideline | 401 and 500 | 400 | A | Open |
| T-38 | R09 manganese above guideline | 0.051 | 0.05 (R10 instead) | A | Open |
| T-39 | R10 manganese near guideline | 0.041 and 0.05 | 0.04 | A | Open |
| T-40 | R09, R10 with manganese blank | never | Blank manganese triggers no manganese rule and is not treated as 0. | A | Open |
| T-41 | R11 private well | Water source Private well | Water source Public supply | A | Open |
| T-42 | R12 all green | Hardness 2.9, iron 0.1, pH 7.5, TDS 300, manganese blank | Same entry with iron 0.27 (one yellow) | A | Open |

## Rule loader checks (design document 2.6)

For each case the tool must stop before assessment and show: "The reference and
recommendation rules could not be loaded. Please try again later."

| ID | Case | Type | Status |
|---|---|---|---|
| T-43 | `parameters.csv` or `recommendations.csv` is missing | A | Open |
| T-44 | A required column is missing from either file | A | Open |
| T-45 | Two rows share the same `parameter_id` or `rule_id` | A | Open |
| T-46 | A rule names a `parameter_id` that is not in `parameters.csv` | A | Open |
| T-47 | A rule references a boundary that is blank for that parameter | A | Open |
| T-48 | A threshold is not a number | A | Open |
| T-49 | A condition uses an unsupported operator or free-form code | A | Open |

## Non-functional requirements

| ID | Req | Check | Pass when | Type | Status |
|---|---|---|---|---|---|
| T-50 | NFR-1 Usability | Three people who have not seen the tool each enter a sample report. | Each reaches the results screen in under three minutes without asking a question. | M | Open |
| T-51 | NFR-2 Performance | Submit the standard entry ten times on a standard laptop. | Every result appears in five seconds or less. | M | Open |
| T-52 | NFR-3 Reliability | Enter the standard entry three times on two devices. | All six results screens are identical. | A and M | Open |
| T-53 | NFR-4 Privacy | Inspect the form. Submit, close the browser, reopen. | No name, address, email, or phone field. Previous values are gone. No file is written. | M | Open |
| T-54 | NFR-5 Compatibility | Run the standard entry in Chrome, Edge, Firefox, Safari, and on one phone. | Form, results screen, and print preview display correctly in all five. | M | Open |
| T-55 | NFR-6 Maintainability | Change iron `yellow_max` in `parameters.csv` from 0.30 to 0.50, restart, enter iron 0.40. Change it back. | Shows yellow instead of red with no code edit, then red again. | A and M | Open |

## Open questions found while writing these cases

1. **Yellow pH has no rule.** pH between 6.5 and 6.9, or between 8.1 and 8.5, is yellow, but no
   rule covers it. An entry that is all green except a yellow pH (for example pH 6.8 on a public
   supply) matches no rule, so the user gets the "cannot provide a suggestion" fallback. Hardness,
   iron, TDS, and manganese each have a "monitor" rule for their yellow band. pH probably needs one.
2. **"Very hard" is in FR-3 but not in the data.** FR-3 says hardness is described as soft,
   moderately hard, hard, or very hard. `parameters.csv` has two boundaries (3.5 and 7 gpg), which
   gives three categories. USGS puts "very hard" above about 10.5 gpg. Either add that boundary or
   update FR-3 to three categories.
3. **Requirements wording.** FR-2 and FR-5 in the requirements document give hardness in mg/L.
   The test plan should state that the tool uses gpg and use 8.8 and 2.9.
4. **FR-9 depends on the dataset.** T-28 and T-29 cannot be run until `data/public_water_data.csv`
   and the dashboard exist.
