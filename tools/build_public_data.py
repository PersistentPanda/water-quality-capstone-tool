"""Build data/public_water_data.csv for the Power BI dashboard (FR-9).

Downloads public well-water results for one state from the Water Quality Portal
(EPA and USGS data, https://www.waterqualitydata.us), keeps the five measurements
the tool uses, converts units to match the tool, and writes one clean CSV.

Run from the repository folder (Python 3.9+, no extra packages needed):

    python tools/build_public_data.py

Options:
    --state 24            two-digit state FIPS code (24 = Maryland, the default)
    --start 01-01-2015    earliest sample date, MM-DD-YYYY
    --site-type Well      Water Quality Portal site type ("Well" = groundwater wells)
    --results FILE --stations FILE
                          use CSV files already downloaded from the portal
                          instead of downloading (Result and Station downloads)

Each finished download is kept in data/raw/ (not committed). If a download is
dropped, run the same command again: it retries only what is missing. Delete
data/raw/ to force a completely fresh download.

Output columns (design document, Appendix F: AREA and PUBLIC_SAMPLE):
    sample_id, area_id, area_name, state, parameter_id, value, unit,
    sample_date, data_source, below_detection, site_id

Rules applied (design document, Section 2.4):
    - Hardness is converted from mg/L as CaCO3 to grains per gallon (divide by 17.1).
    - Iron and manganese reported in ug/L are converted to mg/L.
    - Rows whose unit cannot be matched to the tool's unit are dropped and counted.
    - A result reported as not detected has a blank value and below_detection = yes.
      It is never turned into zero.
    - Exact duplicate rows are dropped. Rows with an unknown site or county are dropped.
"""
import argparse
import csv
import io
import statistics
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

BASE = "https://www.waterqualitydata.us/data"
OUT_COLUMNS = ["sample_id", "area_id", "area_name", "state", "parameter_id", "value", "unit",
               "sample_date", "data_source", "below_detection", "site_id"]

# Water Quality Portal characteristic names -> the tool's parameter_id
CHARACTERISTICS = {
    "Hardness, Ca, Mg": "hardness",
    "Total hardness": "hardness",
    "Hardness, carbonate": "hardness",
    "Iron": "iron",
    "Manganese": "manganese",
    "pH": "ph",
    "Total dissolved solids": "tds",
}
TOOL_UNIT = {"hardness": "gpg", "iron": "mg/L", "manganese": "mg/L", "ph": "pH", "tds": "mg/L"}
GPG_PER_MGL = 1 / 17.1

RESULT_COLUMNS = ["ActivityIdentifier", "ActivityStartDate", "MonitoringLocationIdentifier",
                  "CharacteristicName", "ResultMeasureValue", "ResultMeasure/MeasureUnitCode",
                  "ResultDetectionConditionText", "ProviderName"]
STATION_COLUMNS = ["MonitoringLocationIdentifier", "StateCode", "CountyCode"]

MARYLAND_COUNTIES = {
    "001": "Allegany", "003": "Anne Arundel", "005": "Baltimore", "009": "Calvert",
    "011": "Caroline", "013": "Carroll", "015": "Cecil", "017": "Charles",
    "019": "Dorchester", "021": "Frederick", "023": "Garrett", "025": "Harford",
    "027": "Howard", "029": "Kent", "031": "Montgomery", "033": "Prince George's",
    "035": "Queen Anne's", "037": "St. Mary's", "039": "Somerset", "041": "Talbot",
    "043": "Washington", "045": "Wicomico", "047": "Worcester", "510": "Baltimore City",
}
STATE_ABBR = {"24": "MD"}


def convert(parameter_id, raw_value, raw_unit):
    """Return (value, unit) in the tool's unit, or None if the unit is not usable."""
    unit = (raw_unit or "").strip().lower().replace(" ", "")
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None
    if parameter_id == "ph":
        if unit in ("", "none", "stdunits", "ph", "phunits") and 0 <= value <= 14:
            return round(value, 2), "pH"
        return None
    if value < 0:
        return None
    if parameter_id == "hardness":
        if unit in ("mg/l", "mg/lcaco3", "mg/lascaco3", "ppm"):
            return round(value * GPG_PER_MGL, 2), "gpg"
        if unit in ("gr/gal", "gpg", "grains/gal"):
            return round(value, 2), "gpg"
        return None
    if unit in ("mg/l", "ppm"):
        return round(value, 4), "mg/L"
    if unit in ("ug/l", "ppb"):
        return round(value / 1000, 4), "mg/L"
    return None


def read_csv_text(text, required, label):
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return []
    missing = [c for c in required if c not in rows[0]]
    if missing:
        sys.exit(f"The {label} file is missing expected columns: {missing}\n"
                 f"Columns found: {list(rows[0].keys())}")
    return rows


CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
ATTEMPTS = 4


def _unpack(payload):
    """The portal sends a zip holding one CSV when zip=yes. Return the CSV text."""
    if payload[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            payload = archive.read(archive.namelist()[0])
    return payload.decode("utf-8-sig", errors="replace")


def download(endpoint, params, label):
    """Download one portal file, with retries. Finished downloads are kept in data/raw/
    so a rerun after a dropped connection picks up where it left off.
    Returns the CSV text, or None if every attempt failed."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() else "_" for ch in label)
    cache_file = CACHE_DIR / f"{endpoint.lower()}_{safe}.csv"
    if cache_file.exists() and cache_file.stat().st_size > 0:
        print(f"  {endpoint}: {label} (already downloaded)", flush=True)
        return cache_file.read_text(encoding="utf-8")
    query = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params)
    url = f"{BASE}/{endpoint}/search?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "water-quality-capstone-tool"})
    for attempt in range(1, ATTEMPTS + 1):
        print(f"  {endpoint}: {label} (attempt {attempt} of {ATTEMPTS}) ...", flush=True)
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                text = _unpack(response.read())
            cache_file.write_text(text, encoding="utf-8")
            return text
        except (OSError, zipfile.BadZipFile) as error:
            print(f"    did not finish: {error}", flush=True)
            if attempt < ATTEMPTS:
                time.sleep(15 * attempt)
    print(f"    giving up on {label} for now. Run the command again later to retry just this part.\n"
          f"    Address: {url}", flush=True)
    return None


def build(result_rows, station_rows, state_fips):
    """Turn portal rows into clean output rows. Returns (rows, counts)."""
    county_of = {}
    for s in station_rows:
        county_of[s["MonitoringLocationIdentifier"]] = (s.get("StateCode", "").strip().zfill(2),
                                                         s.get("CountyCode", "").strip().zfill(3))
    counts = defaultdict(int)
    seen = set()
    out = []
    for r in result_rows:
        parameter_id = CHARACTERISTICS.get(r["CharacteristicName"].strip())
        if parameter_id is None:
            counts["other characteristic"] += 1
            continue
        site = r["MonitoringLocationIdentifier"].strip()
        state, county = county_of.get(site, ("", ""))
        if state != state_fips or (state_fips == "24" and county not in MARYLAND_COUNTIES):
            counts["unknown site or county"] += 1
            continue
        raw_value = (r.get("ResultMeasureValue") or "").strip()
        detection = (r.get("ResultDetectionConditionText") or "").strip()
        if raw_value == "":
            if detection:
                value, unit, below = "", TOOL_UNIT[parameter_id], "yes"
            else:
                counts["no value"] += 1
                continue
        else:
            converted = convert(parameter_id, raw_value, r.get("ResultMeasure/MeasureUnitCode"))
            if converted is None:
                counts["unit not usable"] += 1
                continue
            value, unit, below = converted[0], converted[1], "no"
        key = (site, parameter_id, r["ActivityStartDate"], value, r["ActivityIdentifier"])
        if key in seen:
            counts["duplicate"] += 1
            continue
        seen.add(key)
        area_name = MARYLAND_COUNTIES.get(county, county) if state_fips == "24" else county
        out.append({
            "sample_id": f"{r['ActivityIdentifier'].strip()}|{parameter_id}",
            "area_id": f"{state}{county}",
            "area_name": area_name,
            "state": STATE_ABBR.get(state, state),
            "parameter_id": parameter_id,
            "value": value,
            "unit": unit,
            "sample_date": r["ActivityStartDate"].strip(),
            "data_source": f"Water Quality Portal ({(r.get('ProviderName') or '').strip() or 'provider not given'})",
            "below_detection": below,
            "site_id": site,
        })
        counts["kept"] += 1
    out.sort(key=lambda x: (x["area_name"], x["parameter_id"], x["sample_date"], x["sample_id"]))
    return out, counts


def summarize(rows):
    groups = defaultdict(list)
    for r in rows:
        if r["value"] != "":
            groups[(r["area_name"], r["parameter_id"])].append(float(r["value"]))
    print(f"\n{'Area':<18}{'Measurement':<12}{'Samples':>8}{'Median':>10}  Unit")
    for (area, pid), values in sorted(groups.items()):
        print(f"{area:<18}{pid:<12}{len(values):>8}{statistics.median(values):>10.2f}  {TOOL_UNIT[pid]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--state", default="24")
    parser.add_argument("--start", default="01-01-2015")
    parser.add_argument("--site-type", default="Well")
    parser.add_argument("--results")
    parser.add_argument("--stations")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "data" / "public_water_data.csv"))
    args = parser.parse_args()

    if bool(args.results) != bool(args.stations):
        sys.exit("Give both --results and --stations, or neither.")
    if args.results:
        result_text = [Path(args.results).read_text(encoding="utf-8-sig", errors="replace")]
        station_text = Path(args.stations).read_text(encoding="utf-8-sig", errors="replace")
    else:
        common = [("statecode", f"US:{args.state}"), ("siteType", args.site_type),
                  ("startDateLo", args.start), ("mimeType", "csv"), ("zip", "yes"), ("sorted", "no")]
        tag = f"{args.state}_{args.site_type}_{args.start}"
        print("Downloading from the Water Quality Portal. This can take several minutes.")
        station_text = download("Station", [("statecode", f"US:{args.state}"), ("siteType", args.site_type),
                                            ("mimeType", "csv"), ("zip", "yes"), ("sorted", "no")],
                                f"stations_{args.state}_{args.site_type}")
        if station_text is None:
            sys.exit("The station list could not be downloaded, so samples cannot be matched to counties. "
                     "Run the command again in a few minutes.")
        result_text, failed = [], []
        for name in CHARACTERISTICS:
            text = download("Result", common + [("characteristicName", name)], f"{name}_{tag}")
            if text is None:
                failed.append(name)
            else:
                result_text.append(text)
        if failed:
            print(f"\nNOT DOWNLOADED: {', '.join(failed)}. The output file below is incomplete. "
                  f"Run the same command again to fetch only the missing part.")

    station_rows = read_csv_text(station_text, STATION_COLUMNS, "Station")
    result_rows = []
    for text in result_text:
        result_rows += read_csv_text(text, RESULT_COLUMNS, "Result")
    if not result_rows:
        sys.exit("No results came back. Try an earlier --start date or a different --site-type.")

    rows, counts = build(result_rows, station_rows, args.state)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nRead {len(result_rows)} result rows. Wrote {counts['kept']} rows to {out_path}")
    for reason in ("duplicate", "unit not usable", "unknown site or county", "no value", "other characteristic"):
        if counts[reason]:
            print(f"  dropped, {reason}: {counts[reason]}")
    summarize(rows)


if __name__ == "__main__":
    main()
