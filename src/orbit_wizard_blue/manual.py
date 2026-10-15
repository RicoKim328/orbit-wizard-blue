"""Immutable manual GCRS initial conditions and reproducible source snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from math import cos, hypot, isfinite, radians
from numbers import Real

from .models import DataSnapshot, ValidationError


MU = 398600.4418  # km^3 / s^2
EARTH_RADIUS_KM = 6378.137
J2 = 1.08262668e-3


@dataclass(frozen=True)
class KeplerianElements:
    a_km: float
    e: float
    i_deg: float
    raan_deg: float
    argp_deg: float
    true_anomaly_deg: float


@dataclass(frozen=True)
class ConstantAcceleration:
    vector_m_s2: tuple[float, float, float]
    frame: str
    start_utc: datetime
    end_utc: datetime

    def __post_init__(self) -> None:
        if isinstance(self.vector_m_s2, (list, tuple)):
            object.__setattr__(self, "vector_m_s2", tuple(self.vector_m_s2))


@dataclass(frozen=True)
class ManualOrbitInput:
    name: str
    epoch_utc: datetime
    elements: KeplerianElements | None = None
    position_km: tuple[float, float, float] | None = None
    velocity_km_s: tuple[float, float, float] | None = None
    gravity_model: str = "J2"
    acceleration: ConstantAcceleration | None = None

    def __post_init__(self) -> None:
        for field_name in ("position_km", "velocity_km_s"):
            value = getattr(self, field_name)
            if isinstance(value, (list, tuple)):
                object.__setattr__(self, field_name, tuple(value))


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValidationError(f"{label} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(f"{label} must be a finite number") from exc
    if not isfinite(number):
        raise ValidationError(f"{label} must be a finite number")
    return number


def _vector(value: object, label: str) -> tuple[float, float, float]:
    if not isinstance(value, tuple) or len(value) != 3:
        raise ValidationError(f"{label} must contain three numbers")
    return tuple(_finite(component, label) for component in value)  # type: ignore[return-value]


def _utc(value: object, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValidationError(f"{label} must be a timezone-aware UTC datetime")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def validate_manual_input(value: ManualOrbitInput) -> ManualOrbitInput:
    """Validate one bound, Earth-clearance-aware manual initial condition."""
    if not isinstance(value, ManualOrbitInput):
        raise ValidationError("Manual input must be a ManualOrbitInput")
    if not isinstance(value.name, str) or not value.name.strip() or len(value.name) > 200:
        raise ValidationError("Manual satellite name must be 1–200 characters")
    if any(ord(char) < 32 for char in value.name):
        raise ValidationError("Manual satellite name contains control characters")
    epoch = _utc(value.epoch_utc, "Epoch")
    if value.gravity_model not in ("two_body", "J2"):
        raise ValidationError("Gravity model must be two_body or J2")

    has_elements = value.elements is not None
    has_state = value.position_km is not None or value.velocity_km_s is not None
    if has_elements == has_state:
        raise ValidationError("Supply either Keplerian elements or a Cartesian position/velocity pair")
    if has_elements:
        elements = value.elements
        if not isinstance(elements, KeplerianElements):
            raise ValidationError("Elements must be KeplerianElements")
        a = _finite(elements.a_km, "Semi-major axis")
        eccentricity = _finite(elements.e, "Eccentricity")
        inclination = _finite(elements.i_deg, "Inclination")
        if not 0 <= eccentricity < 1:
            raise ValidationError("Eccentricity must be in [0, 1)")
        if a <= 0:
            raise ValidationError("Semi-major axis must be positive")
        if not 0 <= inclination <= 180:
            raise ValidationError("Inclination must be in [0, 180] degrees")
        for label, angle in (
            ("RAAN", elements.raan_deg), ("Argument of periapsis", elements.argp_deg),
            ("True anomaly", elements.true_anomaly_deg),
        ):
            if not 0 <= _finite(angle, label) < 360:
                raise ValidationError(f"{label} must be in [0, 360) degrees")
        initial_radius = a * (1 - eccentricity * eccentricity) / (
            1 + eccentricity * cos(radians(float(elements.true_anomaly_deg)))
        )
        if initial_radius <= EARTH_RADIUS_KM:
            raise ValidationError("Initial Keplerian position must lie outside Earth")
    else:
        position = _vector(value.position_km, "Position")
        velocity = _vector(value.velocity_km_s, "Velocity")
        radius = hypot(*position)
        speed = hypot(*velocity)
        if not isfinite(radius) or not isfinite(speed):
            raise ValidationError("Cartesian state magnitude must be finite")
        if radius <= EARTH_RADIUS_KM:
            raise ValidationError("Cartesian position must lie outside Earth")
        energy = speed * speed / 2 - MU / radius
        if not isfinite(energy):
            raise ValidationError("Cartesian orbital energy must be finite")
        if not energy < 0:
            raise ValidationError("Cartesian state must be elliptically bound")
        angular_momentum = (
            position[1] * velocity[2] - position[2] * velocity[1],
            position[2] * velocity[0] - position[0] * velocity[2],
            position[0] * velocity[1] - position[1] * velocity[0],
        )
        angular_momentum_magnitude = hypot(*angular_momentum)
        if not isfinite(angular_momentum_magnitude):
            raise ValidationError("Cartesian angular momentum must be finite")
        h_squared = angular_momentum_magnitude * angular_momentum_magnitude
        eccentricity_squared = 1 + 2 * energy * h_squared / MU**2
        if not isfinite(eccentricity_squared) or h_squared <= 0 or eccentricity_squared >= 1:
            raise ValidationError("Cartesian state must have a non-degenerate elliptic orbit")

    acceleration = value.acceleration
    if acceleration is not None:
        if not isinstance(acceleration, ConstantAcceleration):
            raise ValidationError("Acceleration must be ConstantAcceleration")
        _vector(acceleration.vector_m_s2, "Acceleration")
        if acceleration.frame not in ("GCRS", "RTN"):
            raise ValidationError("Acceleration frame must be GCRS or RTN")
        start = _utc(acceleration.start_utc, "Acceleration start")
        end = _utc(acceleration.end_utc, "Acceleration end")
        if start < epoch or end < start:
            raise ValidationError("Acceleration times must be ordered and at or after the epoch")
    return value


def _configuration(value: ManualOrbitInput) -> dict[str, object]:
    elements = value.elements
    acceleration = value.acceleration
    return {
        "name": value.name.strip(),
        "epoch_utc": _iso(value.epoch_utc),
        "gravity_model": value.gravity_model,
        "elements": None if elements is None else {
            "a_km": float(elements.a_km), "e": float(elements.e),
            "i_deg": float(elements.i_deg), "raan_deg": float(elements.raan_deg),
            "argp_deg": float(elements.argp_deg), "true_anomaly_deg": float(elements.true_anomaly_deg),
        },
        "position_km": None if value.position_km is None else [float(x) for x in value.position_km],
        "velocity_km_s": None if value.velocity_km_s is None else [float(x) for x in value.velocity_km_s],
        "acceleration": None if acceleration is None else {
            "vector_m_s2": [float(x) for x in acceleration.vector_m_s2],
            "frame": acceleration.frame,
            "start_utc": _iso(acceleration.start_utc),
            "end_utc": _iso(acceleration.end_utc),
        },
    }


def manual_snapshot(value: ManualOrbitInput) -> DataSnapshot:
    """Capture complete normalized input with a stable content hash."""
    validate_manual_input(value)
    configuration = _configuration(value)
    canonical = json.dumps(configuration, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    digest = sha256(canonical.encode("utf-8")).hexdigest()
    instant = _iso(datetime.now(timezone.utc))
    source_format = "osculating_elements" if value.elements is not None else "cartesian_state"
    payload = {
        "OBJECT_NAME": configuration["name"],
        "NORAD_CAT_ID": "",
        "EPOCH": configuration["epoch_utc"],
        "CENTER_NAME": "EARTH",
        "REF_FRAME": "GCRS",
        "TIME_SYSTEM": "UTC",
        "MEAN_ELEMENT_THEORY": "NUMERICAL",
        "GRAVITY_MODEL": value.gravity_model,
        "MANUAL_INPUT": configuration,
    }
    return DataSnapshot(
        payload=payload,
        source_url=f"manual://{digest}",
        fetched_at=instant,
        checked_at=instant,
        sha256=digest,
        source_kind="manual",
        source_format=source_format,
        source_metadata={"manual_input": configuration, "constants": {
            "mu_km3_s2": MU, "earth_radius_km": EARTH_RADIUS_KM, "j2": J2,
        }},
    )
