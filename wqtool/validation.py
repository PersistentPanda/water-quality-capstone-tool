"""FR-1 validation. No file writes, network calls, or shared user-data cache."""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Mapping, Optional

MEASUREMENTS = ("hardness", "iron", "ph", "tds", "manganese")
LABELS = {"hardness": "hardness", "iron": "iron", "ph": "pH", "tds": "TDS", "manganese": "manganese"}
SOURCES = ("Private well", "Public supply")

@dataclass(frozen=True)
class TestEntry:
    hardness: float
    iron: float
    ph: float
    tds: float
    manganese: Optional[float]
    household_size: int
    water_source: str

@dataclass
class ValidationResult:
    is_valid: bool
    messages: list[str] = field(default_factory=list)
    entry: Optional[TestEntry] = None


def validate(entry: Mapping[str, object]) -> ValidationResult:
    """Validate raw form values and return a normalized entry only on success.

    A blank optional manganese reading stays None; zero is an entered reading.
    There is no arbitrary upper concentration or household-size limit.
    """
    messages = []
    clean = {}
    for key in (*MEASUREMENTS, "household_size"):
        raw = entry.get(key)
        text = "" if raw is None else str(raw).strip()
        label = LABELS.get(key, "household size")
        if not text:
            if key == "manganese":
                clean[key] = None
            else:
                messages.append(f"Please enter the {label} result before continuing." if key != "household_size" else "Enter the number of people as a whole number of at least 1.")
            continue
        try:
            number = Decimal(text)
            if not number.is_finite():
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            messages.append(f"Enter a number for {label}, such as 300." if key != "household_size" else "Enter the number of people as a whole number of at least 1.")
            continue
        if key == "household_size":
            if number < 1 or number != number.to_integral_value():
                messages.append("Enter the number of people as a whole number of at least 1.")
            elif number.adjusted() > 300:
                messages.append("Enter a smaller, representable whole number for household size.")
            else:
                clean[key] = int(number)
        elif key == "ph" and not 0 <= number <= 14:
            messages.append("Enter pH between 0 and 14.")
        elif key != "ph" and number < 0:
            messages.append(f"Enter a {label} value of zero or greater.")
        else:
            value = float(number)
            if value == float("inf") or (number != 0 and value == 0):
                messages.append(f"Enter a representable number for {label}.")
            else:
                clean[key] = value
    source = entry.get("water_source")
    if source not in SOURCES:
        messages.append("Select either Private well or Public supply.")
    else:
        clean["water_source"] = source
    if messages:
        return ValidationResult(False, messages)
    return ValidationResult(True, entry=TestEntry(**clean))
