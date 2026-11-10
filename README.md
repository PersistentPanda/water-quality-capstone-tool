# Water Quality Capstone Tool

APTC 495 Applied Technology Capstone, UMGC, Fall 2026.
Team: Daniel Nease, Cecilia Jeong, Hector Djiechieu, James Stallings.

A small Streamlit web app that reads a home water test (hardness, iron, pH, TDS, optional manganese),
compares each value to the EPA secondary drinking water standards (USGS categories for hardness),
shows a red/yellow/green status with a plain-language explanation, recommends a treatment from a fixed
rule set, and produces a printable summary. A separate Power BI dashboard shows public water data by area.

The tool does not test for health contaminants (lead, arsenic, nitrates, bacteria, PFAS) and never
describes water as safe. Every result carries the lab-testing warning (FR-8).

## Layout

```
app.py                      Streamlit page: input form and validation so far (FR-1, FR-2); results and print to come
wqtool/validation.py        Validator (FR-1). Rule loader, Classifier, and Recommender to come (FR-3 to FR-6)
data/parameters.csv         One row per measurement: reference values, color boundaries, explanation text (Daniel)
data/recommendations.csv    Twelve treatment rules; conditions reference parameters.csv columns (see docs/recommendation_rules_v1.md)
data/public_water_data.csv  Cleaned EPA/USGS data for the Power BI dashboard (Cecilia, James, to be added)
tests/                      Test cases written against the requirements document (James)
docs/                       Requirements document and design document
```

## Run it

```
pip install -r requirements.txt
streamlit run app.py
```

## Run the tests

```
python -m pytest tests/
```

## Branching (design document, Section 2.9)

- `main` always runs. No direct commits to main.
- One branch per requirement: `fr-1-validation`, `fr-5-recommender`, `fr-9-dashboard`, and so on.
- Merge through a pull request reviewed by one other team member.
- Changes to the CSV rule files go through the same review.
- Tags: `v0.1` Week 4 check-in, `v0.5` feature-complete, `v1.0` final presentation.

## Editing the rules

Thresholds, reference values, explanations, and treatment rules live in `data/`, not in code.
Edit the CSV, restart the app, and the change takes effect (NFR-6).

### parameters.csv columns

| Column | Meaning |
|---|---|
| parameter_id | short key used in code and rules (hardness, iron, ph, tds, manganese) |
| display_name, unit | what the user sees |
| required | true/false; manganese is optional and blank means "not provided," not zero |
| reference_source | EPA secondary standard or USGS hardness classification |
| reference_low, reference_high | the published limit used for comparison text; blank where none applies |
| green_max, yellow_max | upper color boundaries (display rules, not standards) |
| low_yellow_below, low_red_below | lower color boundaries, used for pH only |
| what_it_measures, within_text, above_text, below_text | plain-language explanation pieces |

Boundaries are inclusive on the upper side: a value equal to green_max is green, equal to yellow_max is yellow.

Hardness is entered in grains per gallon (gpg), the unit on most residential test reports.
Its color bands follow the USGS classification (soft to 3.5, moderately hard to 7, hard above 7). The explanation text
notes that treatment providers often discuss softening from about 2 gpg, but the tool's colors and rules use USGS.
