import pytest
from wqtool.validation import validate

BASE = dict(hardness="150", iron="0.2", ph="7.2", tds="300", manganese="0.02", household_size="4", water_source="Private well")

def test_fr2_sample_round_trip():
    result = validate(BASE)
    assert result.is_valid
    assert vars(result.entry) == dict(hardness=150.0, iron=0.2, ph=7.2, tds=300.0, manganese=0.02, household_size=4, water_source="Private well")

@pytest.mark.parametrize("field", ["hardness", "iron", "ph", "tds", "household_size"])
def test_required(field):
    result = validate({**BASE, field: " "})
    assert not result.is_valid and result.entry is None

@pytest.mark.parametrize("field", ["hardness", "iron", "tds", "manganese"])
def test_negative_concentrations(field):
    assert not validate({**BASE, field: "-0.01"}).is_valid
    assert validate({**BASE, field: "0"}).is_valid

@pytest.mark.parametrize("value,valid", [("0", True), ("14", True), ("-0.01", False), ("15", False)])
def test_ph_boundaries(value, valid):
    assert validate({**BASE, "ph": value}).is_valid == valid

@pytest.mark.parametrize("value", ["0", "-1", "2.5", "NaN", "Infinity", "people"])
def test_bad_household(value):
    assert not validate({**BASE, "household_size": value}).is_valid

@pytest.mark.parametrize("value", ["", " ", None])
def test_optional_blank(value):
    result = validate({**BASE, "manganese": value})
    assert result.is_valid and result.entry.manganese is None

@pytest.mark.parametrize("value", ["NaN", "Infinity", "1e9999", "1e-9999", "abc"])
def test_unusable_numeric(value):
    assert not validate({**BASE, "iron": value}).is_valid

def test_multiple_errors_and_no_mutation():
    raw = {**BASE, "iron": "", "ph": "15", "water_source": ""}
    original = raw.copy()
    result = validate(raw)
    assert len(result.messages) == 3 and raw == original
    assert "Enter pH between 0 and 14." in result.messages

def test_public_supply_and_zero_manganese():
    result = validate({**BASE, "water_source": "Public supply", "manganese": "0"})
    assert result.is_valid and result.entry.manganese == 0


# Exact message text. IDs refer to docs/test_cases_v1.md.

def only_message(changes):
    result = validate({**BASE, **changes})
    assert not result.is_valid and result.entry is None
    assert len(result.messages) == 1
    return result.messages[0]


def test_t01_ph_out_of_range_message():
    assert only_message({"ph": "15"}) == "Enter pH between 0 and 14."


def test_t03_blank_iron_message():
    assert only_message({"iron": ""}) == "Please enter the iron result before continuing."


def test_t04_negative_iron_message():
    assert only_message({"iron": "-0.01"}) == "Enter an iron value of zero or greater."


def test_t05_text_in_tds_message():
    assert only_message({"tds": "abc"}) == "Enter a number for TDS, such as 300."


@pytest.mark.parametrize("value", ["0", "-1", "2.5", "people"])
def test_t06_t06b_household_message(value):
    assert only_message({"household_size": value}) == \
        "Enter the number of people as a whole number of at least 1."


def test_t08_missing_water_source_message():
    assert only_message({"water_source": "Select a water source"}) == \
        "Select either Private well or Public supply."
