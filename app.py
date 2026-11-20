"""Water Quality Decision Support Tool: form, results screen, and print summary."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from wqtool.classifier import COLOR_NOTICE
from wqtool.recommender import assess
from wqtool.report import (
    LAB_WARNING as WARNING, household_text, print_component_html, results_table_html,
    sources_text, suggestions_html,
)
from wqtool.rule_loader import RuleLoadError, load_rules
from wqtool.validation import SOURCES, validate

DATA = Path(__file__).resolve().parent / "data"
FIELDS = {
    "hardness": "Hardness (gpg, grains per gallon) *",
    "iron": "Iron (mg/L) *",
    "ph": "pH (0–14) *",
    "tds": "Total dissolved solids — TDS (mg/L) *",
    "manganese": "Manganese (mg/L, optional)",
    "household_size": "Number of people in the household *",
}

@st.cache_resource
def get_ruleset():
    """Load the rule files once at startup. Restart the app to pick up file changes."""
    return load_rules(DATA / "parameters.csv", DATA / "recommendations.csv")


def reset():
    for key in FIELDS:
        st.session_state[key] = ""
    st.session_state["water_source"] = "Select a water source"
    st.session_state.pop("validated_entry", None)

st.set_page_config(page_title="Water Quality Decision Support Tool", page_icon="💧")
st.title("Water Quality Decision Support Tool")
st.write("Enter the values from your water test report. Fields marked * are required.")
st.caption("Hardness is in grains per gallon (gpg). Iron, TDS, and manganese are in milligrams per liter (mg/L). "
           "pH has no unit.")
try:
    ruleset = get_ruleset()
except RuleLoadError as error:
    st.error(str(error))
    st.stop()
with st.form("water_test", clear_on_submit=False):
    raw = {}
    for key, label in FIELDS.items():
        raw[key] = st.text_input(label, key=key)
    raw["water_source"] = st.selectbox("Water source *", ["Select a water source", *SOURCES], key="water_source")
    submitted = st.form_submit_button("Assess")

if submitted:
    st.session_state.pop("validated_entry", None)
    checked = validate(raw)
    if not checked.is_valid:
        for message in checked.messages:
            st.error(message)
    else:
        st.session_state["validated_entry"] = checked.entry

if "validated_entry" in st.session_state:
    entry = st.session_state["validated_entry"]
    st.success("Your entries are valid.")
    st.subheader("Submitted values")
    rows = []
    for key in FIELDS:
        value = getattr(entry, key)
        rows.append({"Field": FIELDS[key].replace(" *", ""), "Entered value": "Not provided" if value is None else str(value)})
    rows.append({"Field": "Water source", "Entered value": entry.water_source})
    st.table(rows)
    st.caption("These are the last submitted values. After changing the form, select Assess again to update them.")

    assessment = assess(entry, ruleset)
    st.subheader("Your results")
    st.write(household_text(entry))
    st.markdown(results_table_html(assessment.results), unsafe_allow_html=True)
    st.caption(COLOR_NOTICE)
    st.subheader("Suggestions to discuss with a professional")
    st.markdown(suggestions_html(assessment), unsafe_allow_html=True)
    st.caption(sources_text(assessment.results))
    components.html(print_component_html(entry, assessment), height=48)

st.button("Start over", on_click=reset)
st.warning(WARNING)
st.caption("Entries are held only in this browser session and are not saved to application files.")
