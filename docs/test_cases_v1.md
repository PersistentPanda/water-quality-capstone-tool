# Test case list v1

Starting point for the Unit 6 test plan document. One or more test cases per requirement
in the requirements document (FR-1 to FR-9, NFR-1 to NFR-6), plus boundary cases for the
fourteen recommendation rules and the rule loader checks from design document Section 2.6.

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
| T-03 | FR-1 | Standard entry with iron left blank | Blocked. Message: "Please enter the iron result before continuing." | A | Done (`test_t03_blank_iron_message`) |
| T-04 | FR-1 | Standard entry with iron -0.01 | Blocked. Message: "Enter an iron value of zero or greater." | A | Done (`test_t04_negative_iron_message`) |
| T-05 | FR-1 | Standard entry with TDS "abc" | Blocked. Message: "Enter a number for TDS, such as 300." | A | Done (`test_t05_text_in_tds_message`) |
| T-06 | FR-1 | Household size 0, -1, 2.5 | Each blocked. Message: "Enter the number of people as a whole number of at least 1." | A | Done (`test_t06_t06b_household_message`) |
| T-06b | FR-1 | Household size "people" (not a number) | Blocked. Message: "Enter the number of people as a whole number of at least 1." Checked separately from the numeric cases. | A | Done (`test_t06_t06b_household_message`) |
| T-07 | FR-1 | Standard entry with manganese blank | Accepted. Manganese shows "Not provided", never 0. | A | Done (`test_optional_blank`) |
| T-08 | FR-1 | No water source selected | Blocked. Message: "Select either Private well or Public supply." | A | Done (`test_t08_missing_water_source_message`) |
| T-09 | FR-1 | Iron blank, pH 15, no water source | Three messages shown together. Nothing is assessed. | A | Done (`test_multiple_errors_and_no_mutation`) |
| T-10 | FR-2 | Standard entry | All seven entries appear correctly in the submitted values, with units shown on the form. | A | Done (`test_fr2_sample_round_trip`) |
| T-11 | FR-2 | Open the form | Hardness label shows gpg. Iron, TDS, manganese show mg/L. Required fields are marked. | M | Open |
| T-12 | FR-3 | Standard entry (TDS 300) | TDS comparison: "Within the EPA secondary drinking water guideline." | A | Done (`test_t12_t13_tds_comparison_text`) |
| T-13 | FR-3 | Standard entry with TDS 600 | TDS comparison: "Above the EPA secondary drinking water guideline of 500 mg/L." | A | Done (`test_t12_t13_tds_comparison_text`) |
| T-14 | FR-3 | Hardness 2.9, then 5, then 8.8, then 12 | Described as soft, moderately hard, hard, very hard (USGS). The source of the comparison is named. | A | Done (`test_t14_hardness_category_names_source`) |
| T-15 | FR-4 | Iron 0.10, 0.27, 0.40 | Green, yellow, red. Each color has a written label. | A | Done (`test_colors`) |
| T-16 | FR-4 | pH 6.0, 6.8, 7.5, 8.3, 9.0 | Red, yellow, green, yellow, red. | A | Done (`test_colors`) |
| T-17 | FR-4 | TDS 300, 450, 600 | Green, yellow, red. | A | Done (`test_colors`) |
| T-18 | FR-4 | Manganese 0.02, 0.045, 0.06, blank | Green, yellow, red, "Not provided" with no color. | A | Done (`test_colors`, `test_t18_blank_manganese_has_no_color`) |
| T-19 | FR-4 | Hardness 2.9, 5, 8.8 | Green, yellow, red. | A | Done (`test_colors`) |
| T-20 | FR-4 | Any results screen | The screen states that colors do not establish drinking-water safety. | M | Done (`test_results_screen_shows_statuses_suggestions_and_warning`) |
| T-21 | FR-5 | Hardness 8.8, iron 0.1, pH 7.2, TDS 200, household 4 | Suggestion shown: "Consider water softening for hardness and scale concerns." The reason names hardness. | A | Done (`test_t21_t22_softening_suggestion`) |
| T-22 | FR-5 | Same as T-21 with hardness 2.9 | The softening suggestion does not appear. | A | Done (`test_t21_t22_softening_suggestion`) |
| T-23 | FR-5 | Standard entry, run twice | Same suggestions both times, in the same order. | A | Done (`test_t23_same_input_same_output`) |
| T-24 | FR-6 | All five measurements entered | Five explanations appear, one per measurement, each one or two sentences. | A | Done (`test_t24_five_explanations`) |
| T-25 | FR-6 | Iron 0.4 | Explanation says the result is above the EPA secondary guideline and mentions staining or metallic taste. | A | Done (`test_t25_iron_above_explanation`) |
| T-26 | FR-7 | Standard entry, then select "Print summary" once | Print preview is one page. Values, statuses, explanations, suggestions, sources, and the warning match the results screen. | M | Partly (`test_t26_summary_matches_the_results` checks the content; the one-page print preview is a manual check) |
| T-27 | FR-8 | An all-green entry and an entry with at least one red | Both results screens and both printed summaries show the full laboratory warning, word for word. | A and M | Partly (`test_t27_summary_always_carries_the_warning` and the results screen test; the printed page is a manual check) |
| T-28 | FR-9 | Dashboard, select area A, then area B | Only the selected area's records appear. Source, units, and sample dates are shown. Hardness is in gpg. | M | Open |
| T-28b | FR-9 | Dashboard, select Garrett County | Medians match the values computed from `data/public_water_data.csv`: hardness 4.1 gpg (113 samples), iron 0.16 mg/L (97), pH 7.8 (125), TDS 152.5 mg/L (110). Blank (not detected) values are left out of the median. The sample count is shown beside each median. | M | Open |
| T-29 | FR-9 | An area with one measurement missing | Dashboard shows "No data" for it, not zero. | M | Open |

## Recommendation rule boundaries (FR-5)

Each row gives a value that must trigger the rule and the nearest value that must not.
All other measurements are held at green values unless stated.

| ID | Rule | Triggers at | Does not trigger at | Type | Status |
|---|---|---|---|---|---|
| T-30 | R01 hardness, hard | 7.1 gpg | 7.0 gpg (R02 instead) | A | Done (`test_rule_boundaries`) |
| T-31 | R02 hardness, moderately hard | 3.6 and 7.0 gpg | 3.5 gpg | A | Done (`test_rule_boundaries`) |
| T-32 | R03 iron above guideline | 0.31 | 0.30 (R04 instead) | A | Done (`test_rule_boundaries`) |
| T-33 | R04 iron near guideline | 0.25 and 0.30 | 0.24 | A | Done (`test_rule_boundaries`) |
| T-34 | R05 low pH | 6.4 | 6.5 | A | Done (`test_rule_boundaries`) |
| T-35 | R06 high pH | 8.6 | 8.5 | A | Done (`test_rule_boundaries`) |
| T-36 | R07 TDS above guideline | 501 | 500 (R08 instead) | A | Done (`test_rule_boundaries`) |
| T-37 | R08 TDS near guideline | 401 and 500 | 400 | A | Done (`test_rule_boundaries`) |
| T-38 | R09 manganese above guideline | 0.051 | 0.05 (R10 instead) | A | Done (`test_rule_boundaries`) |
| T-39 | R10 manganese near guideline | 0.041 and 0.05 | 0.04 | A | Done (`test_rule_boundaries`) |
| T-40 | R09, R10 with manganese blank | never | Blank manganese triggers no manganese rule and is not treated as 0. | A | Done (`test_t40_blank_manganese_triggers_no_manganese_rule`) |
| T-41 | R11 private well | Water source Private well | Water source Public supply | A | Done (`test_t41_private_well_rule`) |
| T-42 | R12 all green | Hardness 2.9, iron 0.1, pH 7.5, TDS 300, manganese blank | Same entry with iron 0.27 (one yellow) | A | Done (`test_t42_all_green_rule`) |
| T-42b | R12 and pH | never when pH is yellow or red | Same all-green entry with pH 6.8 (yellow, low side), pH 8.3 (yellow, high side), pH 6.0 (red, low), or pH 9.0 (red, high). R12 must not trigger in any of the four. | A | Done (`test_t42b_all_green_never_with_yellow_or_red_ph`) |
| T-42c | R11 with R12 | All-green entry with water source Private well shows both R11 and R12 | Same entry with Public supply shows R12 only | A | Done (`test_t42c_private_well_and_all_green_together`) |
| T-56 | R13 pH low side, yellow | 6.5 and 6.9 | 6.4 (R05 instead) and 7.0 | A | Done (`test_rule_boundaries`, `test_yellow_ph_rules_replace_neighbors_at_the_edges`) |
| T-57 | R14 pH high side, yellow | 8.1 and 8.5 | 8.0 and 8.6 (R06 instead) | A | Done (`test_rule_boundaries`, `test_yellow_ph_rules_replace_neighbors_at_the_edges`) |
| T-58 | Hardness "very hard" (FR-3) | 10.6 gpg is described as very hard | 10.5 gpg is described as hard. Both are red. | A | Done (`test_t58_very_hard_boundary_from_rule_file`) |

## Rule loader checks (design document 2.6)

For each case the loader raises an error whose message is the text below. Showing it on the page
is part of the results screen work. The tool must stop before assessment and show: "The reference and
recommendation rules could not be loaded. Please try again later."

| ID | Case | Type | Status |
|---|---|---|---|
| T-43 | `parameters.csv` or `recommendations.csv` is missing | A | Done (`test_missing_file`) |
| T-44 | A required column is missing from either file | A | Done (`test_required_column`) |
| T-45 | Two rows share the same `parameter_id` or `rule_id` | A | Done (`test_duplicate_identifier`) |
| T-46 | A rule names a `parameter_id` that is not in `parameters.csv` | A | Done (`test_unknown_parameter_reference`) |
| T-47 | A rule references a boundary that is blank for that parameter | A | Done (`test_referenced_optional_boundary_is_required`) |
| T-48 | A threshold is not a usable number: text, blank where required, NaN, or infinity | A | Done (`test_unusable_numeric_boundary`) |
| T-49 | A condition uses an unsupported operator or free-form code | A | Done (`test_unsupported_or_mismatched_condition`) |

## Non-functional requirements

| ID | Req | Check | Pass when | Type | Status |
|---|---|---|---|---|---|
| T-50 | NFR-1 Usability | Three people who have not seen the tool each enter a sample report. | Each reaches the results screen in under three minutes without asking a question. | M | Open |
| T-51 | NFR-2 Performance | Submit the standard entry ten times on a standard laptop. | Every result appears in five seconds or less. | M | Open |
| T-52 | NFR-3 Reliability | Enter the standard entry three times on two devices. | All six results screens are identical. | A and M | Open |
| T-53 | NFR-4 Privacy | Inspect the form. Submit, close the browser, reopen. | No name, address, email, or phone field. Previous values are gone. No file is written. | M | Open |
| T-54 | NFR-5 Compatibility | Run the standard entry in Chrome, Edge, Firefox, Safari, and on one phone. | Form, results screen, and print preview display correctly in all five. | M | Open |
| T-55 | NFR-6 Maintainability | Change iron `yellow_max` in `parameters.csv` from 0.30 to 0.50, restart, enter iron 0.40. Change it back. | Shows yellow instead of red with no code edit, then red again. | A and M | Partly (`test_t55_threshold_change_needs_no_code_edit` covers the automated half; the browser check is open) |

## Open questions found while writing these cases

Questions 1 and 2 were closed on Nov 17 by the rule file change in pull request #7.

1. **Yellow pH had no rule. Closed.** Rules R13 and R14 now give a monitoring suggestion for pH
   from 6.5 to below 7.0 and from above 8.0 to 8.5. See T-56 and T-57.
2. **"Very hard" was in FR-3 but not in the data. Closed.** `parameters.csv` now has a
   `very_high_above` boundary of 10.5 gpg for hardness. See T-14 and T-58.
3. **Requirements wording.** FR-2 and FR-5 in the requirements document give hardness in mg/L.
   The test plan should state that the tool uses gpg and use 8.8 and 2.9.
4. **FR-9 depends on the dataset.** T-28 and T-29 cannot be run until `data/public_water_data.csv`
   and the dashboard exist.
