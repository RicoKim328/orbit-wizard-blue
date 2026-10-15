"""Validate CelesTrak GP JSON before it can replace a cached element set."""

from __future__ import annotations

from datetime import datetime, timedelta
import json
from math import isfinite
import re
from typing import Any

from .models import ValidationError


_REQUIRED_NUMERIC = (
    "MEAN_MOTION", "ECCENTRICITY", "INCLINATION", "RA_OF_ASC_NODE",
    "ARG_OF_PERICENTER", "MEAN_ANOMALY",
)
_OPTIONAL_NUMERIC = ("BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT")
_OPTIONAL_INTEGER = ("EPHEMERIS_TYPE", "ELEMENT_SET_NO", "REV_AT_EPOCH")
_ANGULAR = ("RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY")
_OPTIONAL_REFERENCE = {
    "CENTER_NAME": "EARTH",
    "REF_FRAME": "TEME",
    "TIME_SYSTEM": "UTC",
    "MEAN_ELEMENT_THEORY": "SGP4",
}
_EPOCH_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)?$")


def _validate_json_numbers(value: Any) -> None:
    """Reject Python's non-standard NaN/Infinity even in extra GP fields."""
    if isinstance(value, float) and not isfinite(value):
        raise ValidationError("CelesTrak returned non-finite JSON data")
    if isinstance(value, dict):
        for child in value.values():
            _validate_json_numbers(child)
    elif isinstance(value, list):
        for child in value:
            _validate_json_numbers(child)


def _validate_item(item: Any) -> None:
    if not isinstance(item, dict):
        raise ValidationError("CelesTrak returned a non-object GP record")
    _validate_json_numbers(item)
    required = {"NORAD_CAT_ID", "EPOCH", *_REQUIRED_NUMERIC}
    if not required.issubset(item):
        raise ValidationError("CelesTrak returned an incomplete GP record")
    catalog = item["NORAD_CAT_ID"]
    if isinstance(catalog, bool) or not re.fullmatch(r"[0-9]+", str(catalog)) or int(catalog) <= 0:
        raise ValidationError("CelesTrak returned an invalid NORAD ID")

    epoch = item["EPOCH"]
    if not isinstance(epoch, str) or not _EPOCH_PATTERN.fullmatch(epoch):
        raise ValidationError("CelesTrak returned an invalid UTC epoch")
    try:
        parsed = datetime.fromisoformat(epoch.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("CelesTrak returned an invalid UTC epoch") from exc
    if parsed.utcoffset() not in (None, timedelta(0)):
        raise ValidationError("CelesTrak returned a non-UTC epoch")

    numbers: dict[str, float] = {}
    for field in (*_REQUIRED_NUMERIC, *_OPTIONAL_NUMERIC):
        if field not in item:
            continue
        value = item[field]
        if isinstance(value, bool):
            raise ValidationError(f"CelesTrak returned invalid {field}")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValidationError(f"CelesTrak returned invalid {field}") from exc
        if not isfinite(number):
            raise ValidationError(f"CelesTrak returned invalid {field}")
        numbers[field] = number
    if numbers["MEAN_MOTION"] <= 0:
        raise ValidationError("CelesTrak returned invalid MEAN_MOTION")
    if not 0 <= numbers["ECCENTRICITY"] < 1:
        raise ValidationError("CelesTrak returned invalid ECCENTRICITY")
    if not 0 <= numbers["INCLINATION"] <= 180:
        raise ValidationError("CelesTrak returned invalid INCLINATION")
    for field in _ANGULAR:
        if not 0 <= numbers[field] < 360:
            raise ValidationError(f"CelesTrak returned invalid {field}")
    for field, expected in _OPTIONAL_REFERENCE.items():
        if field in item and (not isinstance(item[field], str) or item[field].upper() != expected):
            raise ValidationError(f"CelesTrak returned unsupported {field}")
    for field in _OPTIONAL_INTEGER:
        if field not in item:
            continue
        value = item[field]
        if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
            raise ValidationError(f"CelesTrak returned invalid {field}")
        if int(value) > 2**31 - 1:
            raise ValidationError(f"CelesTrak returned invalid {field}")
    if "CLASSIFICATION_TYPE" in item and item["CLASSIFICATION_TYPE"] not in ("U", "C", "S"):
        raise ValidationError("CelesTrak returned invalid CLASSIFICATION_TYPE")
    if "OBJECT_ID" in item:
        object_id = item["OBJECT_ID"]
        if not isinstance(object_id, str) or len(object_id) > 64 or any(ord(char) < 32 for char in object_id):
            raise ValidationError("CelesTrak returned invalid OBJECT_ID")


def gp_items(raw: bytes, *, allow_empty: bool = False) -> list[dict[str, Any]]:
    """Decode and validate a GP JSON array, including every search result."""
    if allow_empty and raw.strip() == b"No GP data found":
        return []
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("CelesTrak returned malformed JSON") from exc
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValidationError("CelesTrak returned no satellite records")
    for item in value:
        _validate_item(item)
    return value
