"""Week 4 input/validation prototype: FR-1 and FR-2 integration point."""
import streamlit as st
from wqtool.validation import SOURCES, validate

WARNING = ("This tool does not test for lead, arsenic, nitrates, bacteria, or PFAS "
           "and cannot confirm that water is safe to drink. Use a certified laboratory "
           "to test for these contaminants.")
FIELDS = {
    "hardness": "Hardness (gpg, grains per gallon) *",
    "iron": "Iron (mg/L) *",
    "ph": "pH (0–14) *",
    "tds": "Total dissolved solids — TDS (mg/L) *",
    "manganese": "Manganese (mg/L, optional)",
    "household_size": "Number of people in the household *",
}

def reset():
    for key in FIELDS:
        st.session_state[key] = ""
    st.session_state["water_source"] = "Select a water source"
    st.session_state.pop("validated_entry", None)

st.set_page_config(page_title="Water Quality Decision Support Tool", page_icon="💧")
st.title("Water Quality Decision Support Tool")
st.write("Enter the values from your water test report. Fields marked * are required.")
st.caption("mg/L means milligrams per liter. Hardness is in grains per gallon (gpg); if your report shows "
           "mg/L as CaCO₃, divide by 17.1. pH has no unit.")
st.info("This prototype checks your entries. Water classifications, treatment suggestions, "
        "and the print report will be connected in the next build stage.")
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

st.button("Start over", on_click=reset)
st.warning(WARNING)
st.caption("Entries are held only in this browser session and are not saved to application files.")
