"""Shared, immutable inputs and results for orbit calculations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np
from numpy.typing import NDArray


class ValidationError(ValueError):
    """An input or propagation result cannot produce a valid ephemeris."""


class CancelledError(Exception):
    """The user cancelled a calculation before it completed."""


def freeze_json(value: Any) -> Any:
    """Copy JSON-shaped data into recursively read-only containers."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item) for item in value)
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise TypeError(f"Unsupported metadata value: {type(value).__name__}")


def thaw_json(value: Any) -> Any:
    """Return plain JSON-compatible dicts/lists from frozen model values."""
    if isinstance(value, Mapping):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [thaw_json(item) for item in value]
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise TypeError(f"Unsupported metadata value: {type(value).__name__}")


@dataclass(frozen=True)
class DataSnapshot:
    payload: Mapping[str, Any]
    source_url: str
    fetched_at: str
    checked_at: str
    sha256: str
    stale: bool = False
    warning: str = ""
    source_kind: str = "online"
    source_format: str = "gp_json"
    source_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", freeze_json(self.payload))
        object.__setattr__(self, "source_metadata", freeze_json(self.source_metadata))


@dataclass(frozen=True)
class EarthData:
    iers_path: Path
    leap_seconds_path: Path
    provenance: Mapping[str, Any]
    warning: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "iers_path", Path(self.iers_path))
        object.__setattr__(self, "leap_seconds_path", Path(self.leap_seconds_path))
        object.__setattr__(self, "provenance", freeze_json(self.provenance))


@dataclass(frozen=True)
class OrbitRequest:
    start_utc: datetime
    end_utc: datetime
    step_seconds: int = 60


def _readonly_array(value: NDArray[np.float64] | None, shape: tuple[int, ...]) -> NDArray[np.float64] | None:
    if value is None:
        return None
    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != shape:
        raise ValidationError(f"Expected array shape {shape}, got {array.shape}")
    if not np.isfinite(array).all():
        raise ValidationError("Orbit result arrays must contain only finite values")
    return np.frombuffer(array.tobytes(), dtype=np.float64).reshape(shape)


@dataclass(frozen=True)
class OrbitResult:
    satellite: DataSnapshot
    request: OrbitRequest
    times_utc: tuple[str, ...]
    teme_position_km: NDArray[np.float64] | None
    teme_velocity_km_s: NDArray[np.float64] | None
    itrs_position_km: NDArray[np.float64] | None
    itrs_velocity_km_s: NDArray[np.float64] | None
    gcrs_position_km: NDArray[np.float64] | None
    geodetic_deg_km: NDArray[np.float64] | None
    earth_rotation: NDArray[np.float64] | None
    warnings: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    gcrs_velocity_km_s: NDArray[np.float64] | None = None
    native_frame: str = "TEME"
    elapsed_si_seconds: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        n = len(self.times_utc)
        if not isinstance(self.satellite, DataSnapshot):
            raise ValidationError("Satellite must be a DataSnapshot")
        if self.native_frame not in ("TEME", "GCRS"):
            raise ValidationError("Native frame must be TEME or GCRS")
        if self.native_frame == "TEME" and (self.teme_position_km is None or self.teme_velocity_km_s is None):
            raise ValidationError("TEME native results require position and velocity")
        if self.native_frame == "GCRS" and (self.gcrs_position_km is None or self.gcrs_velocity_km_s is None):
            raise ValidationError("GCRS native results require position and velocity")
        object.__setattr__(self, "times_utc", tuple(self.times_utc))
        object.__setattr__(self, "teme_position_km", _readonly_array(self.teme_position_km, (n, 3)))
        object.__setattr__(self, "teme_velocity_km_s", _readonly_array(self.teme_velocity_km_s, (n, 3)))
        for name in ("itrs_position_km", "itrs_velocity_km_s", "gcrs_position_km", "geodetic_deg_km"):
            object.__setattr__(self, name, _readonly_array(getattr(self, name), (n, 3)))
        object.__setattr__(self, "gcrs_velocity_km_s", _readonly_array(self.gcrs_velocity_km_s, (n, 3)))
        object.__setattr__(self, "earth_rotation", _readonly_array(self.earth_rotation, (n, 3, 3)))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "provenance", freeze_json(self.provenance))
        if self.elapsed_si_seconds is not None:
            elapsed = tuple(round(float(value), 6) for value in self.elapsed_si_seconds)
            if (len(elapsed) != n or not elapsed or elapsed[0] != 0.0
                    or not all(isfinite(value) for value in elapsed)
                    or any(right <= left for left, right in zip(elapsed, elapsed[1:]))):
                raise ValidationError("Elapsed SI seconds must start at zero and increase for each sample")
            object.__setattr__(self, "elapsed_si_seconds", elapsed)
