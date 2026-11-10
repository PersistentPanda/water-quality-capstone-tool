# Input and validation prototype — FR-1 and FR-2

This branch adds app.py, wqtool/validation.py, and focused tests. The form collects
all seven entries, explains units, preserves fields on correction, and shows a
normalized submitted-value preview. Blank manganese stays None. Nonfinite and
unrepresentable numbers are rejected. Start over clears this assessment.

Run from the repository folder:

    python -m pip install -r requirements.txt
    python -m streamlit run app.py

Run checks:

    python -m pytest -q

Validation returns ValidationResult(is_valid, messages, entry). The additional
entry field holds a normalized TestEntry only on success. This extends the design's
validation interface for integration without mutating the submitted input.

User entries use per-session Streamlit state only; they are not cached globally,
logged by this code, or saved to application files. Text fields intentionally allow
invalid and blank entries so the validator can give requirement-specific messages.
Form changes are submitted together on Assess; the preview is explicitly labeled
as the last submitted values.

The validated-entry preview is the Week 4 handoff point for the classifier and
recommender. It does not generate classifications, suggestions, or reports, so it
does not load rule files yet. Before adding those functions, integrate the rule
loader and block actual assessment if the rule files are missing or invalid.
The FR-8 warning is already displayed, but FR-3 through FR-7 are not implemented.

Verification: 32 automated checks passed, including Streamlit AppTest interaction
checks. Desktop/mobile visual review and cross-browser checks remain for the team.
