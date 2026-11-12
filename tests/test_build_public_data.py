"""Checks for tools/build_public_data.py using small sample rows in the portal's column layout."""
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "build_public_data", Path(__file__).resolve().parents[1] / "tools" / "build_public_data.py")
bpd = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bpd)

STATIONS = [
    {"MonitoringLocationIdentifier": "USGS-0001", "StateCode": "24", "CountyCode": "003"},
    {"MonitoringLocationIdentifier": "USGS-0002", "StateCode": "24", "CountyCode": "21"},
    {"MonitoringLocationIdentifier": "USGS-0003", "StateCode": "51", "CountyCode": "059"},
]


def row(site, name, value, unit, act="A1", date="2022-05-01", detect="", provider="NWIS", **extra):
    base = {"ActivityIdentifier": act, "ActivityStartDate": date, "MonitoringLocationIdentifier": site,
            "CharacteristicName": name, "ResultMeasureValue": value, "ResultMeasure/MeasureUnitCode": unit,
            "ResultDetectionConditionText": detect, "ProviderName": provider}
    base.update(extra)
    return base


def build(rows):
    return bpd.build(rows, STATIONS, "24")


def test_hardness_converted_to_gpg():
    out, _ = build([row("USGS-0001", "Hardness, Ca, Mg", "150", "mg/l CaCO3")])
    assert out[0]["parameter_id"] == "hardness" and out[0]["unit"] == "gpg"
    assert out[0]["value"] == round(150 / 17.1, 2) == 8.77
    assert out[0]["area_name"] == "Anne Arundel" and out[0]["area_id"] == "24003" and out[0]["state"] == "MD"


def test_iron_and_manganese_micrograms_to_mg_per_l():
    out, _ = build([row("USGS-0001", "Iron", "310", "ug/l"), row("USGS-0001", "Manganese", "50", "ug/L", act="A2")])
    values = {r["parameter_id"]: (r["value"], r["unit"]) for r in out}
    assert values == {"iron": (0.31, "mg/L"), "manganese": (0.05, "mg/L")}


def test_ph_and_tds_pass_through():
    out, _ = build([row("USGS-0001", "pH", "7.2", "std units"), row("USGS-0001", "Total dissolved solids", "300", "mg/l", act="A2")])
    values = {r["parameter_id"]: (r["value"], r["unit"]) for r in out}
    assert values == {"ph": (7.2, "pH"), "tds": (300.0, "mg/L")}


def test_not_detected_stays_blank_never_zero():
    out, _ = build([row("USGS-0001", "Iron", "", "", detect="Not Detected")])
    assert out[0]["value"] == "" and out[0]["below_detection"] == "yes"


def test_short_county_code_is_padded():
    out, _ = build([row("USGS-0002", "pH", "6.9", "None")])
    assert out[0]["area_name"] == "Frederick"


def test_dropped_rows_are_counted():
    rows = [
        row("USGS-0001", "Iron", "0.2", "mg/l"),
        row("USGS-0001", "Iron", "0.2", "mg/l"),                 # exact duplicate
        row("USGS-0001", "Iron", "5", "tons/day", act="A2"),     # unusable unit
        row("USGS-0003", "Iron", "0.2", "mg/l", act="A3"),       # site in another state
        row("USGS-9999", "Iron", "0.2", "mg/l", act="A4"),       # site not in station file
        row("USGS-0001", "Iron", "", "", act="A5"),              # no value and no detection note
        row("USGS-0001", "Chloride", "12", "mg/l", act="A6"),    # not one of the five measurements
        row("USGS-0001", "pH", "70", "std units", act="A7"),     # impossible pH
    ]
    out, counts = build(rows)
    assert len(out) == 1 and counts["kept"] == 1
    assert counts["duplicate"] == 1 and counts["unit not usable"] == 2
    assert counts["unknown site or county"] == 2 and counts["no value"] == 1
    assert counts["other characteristic"] == 1


def test_missing_column_stops_with_a_clear_message():
    import pytest
    with pytest.raises(SystemExit) as stop:
        bpd.read_csv_text("A,B\n1,2\n", bpd.RESULT_COLUMNS, "Result")
    assert "missing expected columns" in str(stop.value)


def test_one_value_per_sample_field_ph_beats_lab_ph():
    rows = [row("USGS-0001", "pH", "6.6", "std units", USGSPCode="00403"),
            row("USGS-0001", "pH", "5.9", "std units", USGSPCode="00400")]
    out, counts = build(rows)
    assert len(out) == 1 and out[0]["value"] == 5.9
    assert counts["second result for the same sample"] == 1


def test_dissolved_iron_beats_recoverable_and_measured_tds_beats_calculated():
    rows = [row("USGS-0001", "Iron", "900", "ug/l", USGSPCode="01045"),
            row("USGS-0001", "Iron", "310", "ug/l", USGSPCode="01046"),
            row("USGS-0001", "Total dissolved solids", "305", "mg/l", USGSPCode="70301"),
            row("USGS-0001", "Total dissolved solids", "298", "mg/l", USGSPCode="70300")]
    out, _ = build(rows)
    values = {r["parameter_id"]: r["value"] for r in out}
    assert values == {"iron": 0.31, "tds": 298.0}
    assert len({r["sample_id"] for r in out}) == len(out)


def test_replicates_and_surface_water_are_dropped():
    rows = [row("USGS-0001", "pH", "7.0", "std units"),
            row("USGS-0001", "pH", "7.1", "std units", act="A2", ActivityTypeCode="Quality Control Sample-Field Replicate"),
            row("USGS-0001", "pH", "7.2", "std units", act="A3", ActivityMediaSubdivisionName="Surface Water")]
    out, counts = build(rows)
    assert len(out) == 1 and counts["quality-control sample"] == 1 and counts["not groundwater"] == 1
