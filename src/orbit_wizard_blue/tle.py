"""Strict two-line element parsing with lossless source metadata."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from sgp4.api import Satrec
from sgp4.earth_gravity import wgs72
from sgp4.exporter import export_omm
from sgp4.io import twoline2rv as validate_fixed_columns, verify_checksum

from .models import ValidationError


@dataclass(frozen=True)
class ParsedTle:
    """A validated TLE as common GP/OMM fields and original source lines."""

    payload: dict[str, Any]
    metadata: dict[str, Any]


class _ExportWithoutDesignator:
    """Supply export_omm's required designator without inventing source data."""

    intldesg = "00000A"

    def __init__(self, satellite: Satrec) -> None:
        self.satellite = satellite

    def __getattr__(self, name: str) -> Any:
        return getattr(self.satellite, name)


def _parse_pair(name_line: str, line1: str, line2: str) -> ParsedTle:
    for number, line in ((1, line1), (2, line2)):
        if len(line) != 69 or not line.startswith(f"{number} "):
            raise ValidationError(f"TLE line {number} must be exactly 69 characters and start with '{number} '")
        try:
            verify_checksum(line)
        except ValueError as exc:
            raise ValidationError(f"TLE line {number} checksum is invalid: {exc}") from exc
    if line1[2:7] != line2[2:7]:
        raise ValidationError("TLE line 1 and 2 catalog numbers differ")
    try:
        # The C++ reader accepts some malformed fixed columns. The Python
        # reader checks separators and numeric fields before C++ ingestion.
        validate_fixed_columns(line1, line2, wgs72)
        satellite = Satrec.twoline2rv(line1, line2)
        if satellite.error:
            raise ValidationError(f"TLE SGP4 initialization failed with code {satellite.error}")
        name = name_line[2:].strip() if name_line.startswith("0 ") else name_line.strip()
        object_name = name or f"NORAD {satellite.satnum}"
        if satellite.intldesg:
            payload = export_omm(satellite, object_name)
        else:
            payload = export_omm(_ExportWithoutDesignator(satellite), object_name)
            payload["OBJECT_ID"] = ""
        for key in ("MEAN_MOTION", "ECCENTRICITY", "INCLINATION", "RA_OF_ASC_NODE",
                    "ARG_OF_PERICENTER", "MEAN_ANOMALY", "BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT"):
            if not isfinite(float(payload[key])):
                raise ValidationError(f"TLE {key} must be finite")
    except ValidationError:
        raise
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError(f"Invalid TLE orbital elements: {exc}") from exc
    raw_lines = (name_line, line1, line2) if name_line else (line1, line2)
    return ParsedTle(
        payload=payload,
        metadata={
            "name": name,
            "name_line": name_line,
            "line1": line1,
            "line2": line2,
            "raw_tle": "\n".join(raw_lines),
            "catalog_id": satellite.satnum,
        },
    )


def parse_tle(text: str) -> tuple[ParsedTle, ...]:
    """Parse one or more 2-line or named 3-line TLE records in input order."""
    if not isinstance(text, str):
        raise ValidationError("TLE input must be text")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValidationError("TLE input is empty")
    records: list[ParsedTle] = []
    pending_name = ""
    index = 0
    while index < len(lines):
        line = lines[index]
        record_number = len(records) + 1
        if line.startswith("1 "):
            if index + 1 >= len(lines):
                raise ValidationError(f"TLE record #{record_number}: line 1 has no following line 2")
            try:
                records.append(_parse_pair(pending_name, line, lines[index + 1]))
            except ValidationError as exc:
                raise ValidationError(f"TLE record #{record_number}: {exc}") from exc
            pending_name = ""
            index += 2
            continue
        if line.startswith("2 "):
            raise ValidationError(f"TLE record #{record_number}: Unexpected line 2 without preceding line 1")
        if pending_name:
            raise ValidationError(f"TLE record #{record_number}: Multiple name lines before a line 1")
        pending_name = line
        index += 1
    if pending_name:
        raise ValidationError(f"TLE record #{len(records) + 1}: name has no following element pair")
    return tuple(records)
