"""Shared, immutable inputs and results for orbit calculations."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray


class ValidationError(ValueError):
    """An input or propagation result cannot produce a valid ephemeris."""


class CancelledError(Exception):
    """The user cancelled a calculation before it completed."""


@dataclass(frozen=True)
class DataSnapshot:
    payload: dict[str, Any]
    source_url: str
    fetched_at: str
    checked_at: str
    sha256: str
    stale: bool = False
    warning: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", deepcopy(self.payload))


@dataclass(frozen=True)
class EarthData:
    iers_path: Path
    leap_seconds_path: Path
    provenance: dict[str, Any]
    warning: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "iers_path", Path(self.iers_path))
        object.__setattr__(self, "leap_seconds_path", Path(self.leap_seconds_path))
        object.__setattr__(self, "provenance", deepcopy(self.provenance))


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
    return np.frombuffer(array.tobytes(), dtype=np.float64).reshape(shape)


@dataclass(frozen=True)
class OrbitResult:
    satellite: DataSnapshot
    request: OrbitRequest
    times_utc: tuple[str, ...]
    teme_position_km: NDArray[np.float64]
    teme_velocity_km_s: NDArray[np.float64]
    itrs_position_km: NDArray[np.float64] | None
    itrs_velocity_km_s: NDArray[np.float64] | None
    gcrs_position_km: NDArray[np.float64] | None
    geodetic_deg_km: NDArray[np.float64] | None
    earth_rotation: NDArray[np.float64] | None
    warnings: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n = len(self.times_utc)
        object.__setattr__(self, "satellite", deepcopy(self.satellite))
        object.__setattr__(self, "times_utc", tuple(self.times_utc))
        object.__setattr__(self, "teme_position_km", _readonly_array(self.teme_position_km, (n, 3)))
        object.__setattr__(self, "teme_velocity_km_s", _readonly_array(self.teme_velocity_km_s, (n, 3)))
        for name in ("itrs_position_km", "itrs_velocity_km_s", "gcrs_position_km", "geodetic_deg_km"):
            object.__setattr__(self, name, _readonly_array(getattr(self, name), (n, 3)))
        object.__setattr__(self, "earth_rotation", _readonly_array(self.earth_rotation, (n, 3, 3)))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "provenance", deepcopy(self.provenance))
