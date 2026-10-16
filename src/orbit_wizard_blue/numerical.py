"""Offline propagation of manually entered osculating GCRS states."""

from __future__ import annotations

from math import cos, sin, sqrt
from pathlib import Path
from typing import Callable

import numpy as np
from astropy import units as u
from astropy.time import Time
from astropy.utils import iers
from scipy.integrate import solve_ivp

from .manual import EARTH_RADIUS_KM, J2, MU, KeplerianElements, ManualOrbitInput, manual_snapshot, validate_manual_input
from .models import CancelledError, EarthData, OrbitRequest, OrbitResult, ValidationError, thaw_json
from .orbit import (
    _CHUNK, _check_cancel, _check_eop_coverage, _coordinate_chunk_from_gcrs, _earth_context,
    _file_sha256, _iso_utc, _notify, _package_version, _time_grid,
)


_RTOL = 1e-10
_ATOL = np.array([1e-8] * 3 + [1e-11] * 3, dtype=np.float64)
_MAX_INTEGRATION_SPAN_S = 3600.0


def elements_to_state(elements: KeplerianElements) -> tuple[np.ndarray, np.ndarray]:
    """Convert elliptic osculating Kepler elements to a GCRS Cartesian state."""
    a = float(elements.a_km)
    e = float(elements.e)
    inclination, raan, argp, anomaly = np.deg2rad(
        (elements.i_deg, elements.raan_deg, elements.argp_deg, elements.true_anomaly_deg)
    )
    if not np.isfinite((a, e, inclination, raan, argp, anomaly)).all() or a <= 0 or not 0 <= e < 1:
        raise ValidationError("Keplerian elements must define a finite elliptic orbit")
    p = a * (1 - e * e)
    radius = p / (1 + e * cos(anomaly))
    plane_position = np.array((radius * cos(anomaly), radius * sin(anomaly), 0.0))
    factor = sqrt(MU / p)
    plane_velocity = np.array((-factor * sin(anomaly), factor * (e + cos(anomaly)), 0.0))
    co, so = cos(raan), sin(raan)
    ci, si = cos(inclination), sin(inclination)
    cw, sw = cos(argp), sin(argp)
    rotation = np.array((
        (co * cw - so * sw * ci, -co * sw - so * cw * ci, so * si),
        (so * cw + co * sw * ci, -so * sw + co * cw * ci, -co * si),
        (sw * si, cw * si, ci),
    ))
    return rotation @ plane_position, rotation @ plane_velocity


def _acceleration(state: np.ndarray, gravity_model: str, thrust: np.ndarray | None, frame: str) -> np.ndarray:
    position, velocity = state[:3], state[3:]
    radius = float(np.linalg.norm(position))
    if radius <= 0 or not np.isfinite(radius):
        raise ValidationError("Numerical state has invalid radius")
    acceleration = -MU * position / radius**3
    if gravity_model == "J2":
        z_ratio_sq = (position[2] / radius) ** 2
        factor = 1.5 * J2 * MU * EARTH_RADIUS_KM**2 / radius**5
        acceleration += factor * position * np.array((5 * z_ratio_sq - 1, 5 * z_ratio_sq - 1, 5 * z_ratio_sq - 3))
    if thrust is not None:
        if frame == "GCRS":
            acceleration += thrust
        else:
            normal = np.cross(position, velocity)
            normal_norm = np.linalg.norm(normal)
            if normal_norm <= 0 or not np.isfinite(normal_norm):
                raise ValidationError("RTN acceleration requires nonzero orbital angular momentum")
            radial = position / radius
            normal /= normal_norm
            transverse = np.cross(normal, radial)
            acceleration += thrust[0] * radial + thrust[1] * transverse + thrust[2] * normal
    return acceleration


def _initial_state(manual: ManualOrbitInput) -> np.ndarray:
    if manual.elements is not None:
        position, velocity = elements_to_state(manual.elements)
    else:
        position = np.asarray(manual.position_km, dtype=np.float64)
        velocity = np.asarray(manual.velocity_km_s, dtype=np.float64)
    state = np.concatenate((position, velocity))
    if state.shape != (6,) or not np.isfinite(state).all():
        raise ValidationError("Initial GCRS position and velocity must each contain three finite values")
    if np.linalg.norm(position) <= EARTH_RADIUS_KM:
        raise ValidationError("Initial state intersects the Earth reference sphere")
    return state


def _si_timing(
    manual: ManualOrbitInput, instants: tuple, end_utc, earth_data: EarthData | None,
) -> tuple[np.ndarray, float, tuple[float, float] | None, dict[str, str], tuple[str, ...]]:
    """Map UTC labels and burn boundaries to elapsed SI seconds, including leap seconds."""
    bundled = EarthData(Path(iers.IERS_A_FILE), Path(iers.IERS_LEAP_SECOND_FILE), {"kind": "bundled"})
    sources = [earth_data, bundled] if earth_data is not None else [bundled]
    failure = None
    for source in sources:
        try:
            leap_hash = _file_sha256(source.leap_seconds_path)
            with _earth_context(source) as (_, leaps):
                epoch = Time(manual.epoch_utc, scale="utc")
                seconds = np.asarray((Time(instants, scale="utc") - epoch).to_value(u.s), dtype=np.float64)
                duration = float((Time(end_utc, scale="utc") - epoch).to_value(u.s))
                leap_expires = leaps.expires.utc.isot
                expired = Time(end_utc, scale="utc") > leaps.expires
                burn_interval = None
                if manual.acceleration is not None:
                    start = float((Time(manual.acceleration.start_utc, scale="utc") - epoch).to_value(u.s))
                    end = float((Time(manual.acceleration.end_utc, scale="utc") - epoch).to_value(u.s))
                    if end > 0 and start < duration:
                        burn_interval = max(0.0, start), min(duration, end)
            if _file_sha256(source.leap_seconds_path) != leap_hash:
                raise ValueError("Leap-second file changed during numerical timing")
            provenance = {
                "leap_seconds_path_used": str(source.leap_seconds_path),
                "leap_seconds_file_sha256_used": leap_hash,
                "leap_seconds_expires": leap_expires,
            }
            warnings = []
            if failure is not None:
                warnings.append(f"Supplied leap-second data unavailable for numerical timing; bundled table used: {failure}")
            if expired:
                warnings.append("Leap-second table used for numerical timing has expired for the requested period")
            return seconds, duration, burn_interval, provenance, tuple(warnings)
        except (OSError, ValueError, TypeError, IndexError, RuntimeError) as exc:
            failure = exc
    raise ValidationError(f"Could not establish UTC-to-SI-second timing: {failure}")


def _integrate(
    manual: ManualOrbitInput, seconds: np.ndarray, duration: float,
    burn_interval: tuple[float, float] | None, initial: np.ndarray,
    progress: Callable[[int, str], None] | None, cancel: Callable[[], bool] | None,
) -> tuple[np.ndarray, np.ndarray]:
    states = np.empty((len(seconds), 6), dtype=np.float64)
    states[0] = initial
    if duration == 0:
        _notify(progress, 50, "Numerical propagation")
        return states[:, :3], states[:, 3:]

    boundaries = [0.0, duration]
    if burn_interval is not None:
        boundaries.extend(burn_interval)
    boundaries = sorted(set(boundaries))
    thrust = (np.asarray(manual.acceleration.vector_m_s2, dtype=np.float64) / 1000.0
              if manual.acceleration is not None else None)
    frame = manual.acceleration.frame if manual.acceleration is not None else "GCRS"
    cursor = 1
    state = initial.copy()
    rhs_calls = 0

    def impact(_time: float, value: np.ndarray) -> float:
        return float(np.linalg.norm(value[:3]) - EARTH_RADIUS_KM)

    impact.terminal = True  # type: ignore[attr-defined]
    impact.direction = -1  # type: ignore[attr-defined]

    def periapsis(_time: float, value: np.ndarray) -> float:
        return float(np.dot(value[:3], value[3:]))

    periapsis.terminal = False  # type: ignore[attr-defined]
    periapsis.direction = 1  # type: ignore[attr-defined]

    for boundary_start, boundary_end in zip(boundaries[:-1], boundaries[1:]):
        active = (burn_interval is not None and
                  burn_interval[0] <= (boundary_start + boundary_end) / 2 < burn_interval[1])
        applied = thrust if active else None
        segment_start = boundary_start
        while segment_start < boundary_end:
            _check_cancel(cancel)
            segment_end = min(segment_start + _MAX_INTEGRATION_SPAN_S, boundary_end)

            def rhs(_time: float, value: np.ndarray) -> np.ndarray:
                nonlocal rhs_calls
                rhs_calls += 1
                if rhs_calls % 64 == 0:
                    _check_cancel(cancel)
                return np.concatenate((value[3:], _acceleration(value, manual.gravity_model, applied, frame)))

            solution = solve_ivp(
                rhs, (segment_start, segment_end), state, method="DOP853", rtol=_RTOL, atol=_ATOL,
                events=(impact, periapsis), dense_output=True,
            )
            _check_cancel(cancel)
            if not solution.success:
                raise ValidationError(f"Numerical integrator failed at t={solution.t[-1]:.6f} s: {solution.message}")
            if len(solution.t_events[0]):
                raise ValidationError(f"Orbit intersects the Earth reference sphere at t={solution.t_events[0][0]:.6f} s")
            for time, value in zip(solution.t_events[1], solution.y_events[1]):
                if np.linalg.norm(value[:3]) <= EARTH_RADIUS_KM:
                    raise ValidationError(f"Orbit intersects the Earth reference sphere at t={time:.6f} s")
            state = np.asarray(solution.y[:, -1], dtype=np.float64)
            if not np.isfinite(state).all() or np.linalg.norm(state[:3]) <= EARTH_RADIUS_KM:
                raise ValidationError(f"Numerical state is invalid at t={segment_end:.6f} s")
            stop = int(np.searchsorted(seconds, segment_end, side="right"))
            if stop > cursor:
                states[cursor:stop] = solution.sol(seconds[cursor:stop]).T
                if not np.isfinite(states[cursor:stop]).all():
                    raise ValidationError(f"Numerical samples are non-finite near t={segment_end:.6f} s")
                if np.any(np.linalg.norm(states[cursor:stop, :3], axis=1) <= EARTH_RADIUS_KM):
                    raise ValidationError(f"Orbit intersects the Earth reference sphere near t={segment_end:.6f} s")
                cursor = stop
            _notify(progress, min(50, round(50 * segment_end / duration)), "Numerical propagation")
            segment_start = segment_end
    if cursor != len(seconds):
        raise ValidationError("Numerical integration did not cover the UTC grid")
    return states[:, :3], states[:, 3:]


def compute_manual_ephemeris(
    manual: ManualOrbitInput,
    request: OrbitRequest,
    earth_data: EarthData | None,
    progress: Callable[[int, str], None] | None = None,
    cancel: Callable[[], bool] | None = None,
) -> OrbitResult:
    """Integrate a manual GCRS state and convert it with explicit local Earth data."""
    _check_cancel(cancel)
    validate_manual_input(manual)
    instants = _time_grid(request)
    if instants[0] != manual.epoch_utc:
        raise ValidationError("Manual calculation must start at its initial-state epoch")
    snapshot = manual_snapshot(manual)
    _notify(progress, 0, "Numerical propagation")
    seconds, duration, burn_interval, timing_provenance, timing_warnings = _si_timing(
        manual, instants, request.end_utc, earth_data,
    )
    position, velocity = _integrate(
        manual, seconds, duration, burn_interval, _initial_state(manual), progress, cancel,
    )
    n = len(instants)
    teme_p = teme_v = itrs_p = itrs_v = geo = rotation = None
    warnings: list[str] = list(timing_warnings)
    earth_provenance = {} if earth_data is None else thaw_json(earth_data.provenance)
    if earth_data is None:
        warnings.append("Earth orientation data are unavailable; TEME, ITRS, geodetic, and 3D Earth orientation are unavailable")
    else:
        if earth_data.warning:
            warnings.append(earth_data.warning)
        try:
            teme_p = np.empty((n, 3), dtype=np.float64)
            teme_v = np.empty((n, 3), dtype=np.float64)
            itrs_p = np.empty((n, 3), dtype=np.float64)
            itrs_v = np.empty((n, 3), dtype=np.float64)
            geo = np.empty((n, 3), dtype=np.float64)
            rotation = np.empty((n, 3, 3), dtype=np.float64)
            iers_hash = _file_sha256(earth_data.iers_path)
            leaps_hash = _file_sha256(earth_data.leap_seconds_path)
            earth_provenance["iers_file_sha256_used"] = iers_hash
            earth_provenance["leap_seconds_file_sha256_used"] = leaps_hash
            predicted = False
            with _earth_context(earth_data) as (table, leaps):
                earth_provenance["leap_seconds_expires"] = leaps.expires.utc.isot
                if Time(instants[-1], scale="utc") > leaps.expires:
                    warnings.append("Leap-second table has expired for the requested period")
                for left in range(0, n, _CHUNK):
                    _check_cancel(cancel)
                    right = min(left + _CHUNK, n)
                    times = Time(instants[left:right], scale="utc")
                    predicted = _check_eop_coverage(table, times) or predicted
                    values = _coordinate_chunk_from_gcrs(position[left:right], velocity[left:right], times)
                    for label, value, shape in zip(
                        ("TEME position", "TEME velocity", "ITRS position", "ITRS velocity", "geodetic coordinates", "Earth rotation"),
                        values, ((right - left, 3),) * 5 + ((right - left, 3, 3),),
                    ):
                        if np.shape(value) != shape or not np.isfinite(value).all():
                            raise ValueError(f"{label} contains invalid shape or non-finite values")
                    for array, value in zip((teme_p, teme_v, itrs_p, itrs_v, geo, rotation), values):
                        array[left:right] = value
                    _notify(progress, 50 + min(49, round(49 * right / n)), "Coordinate conversion")
            if _file_sha256(earth_data.iers_path) != iers_hash or _file_sha256(earth_data.leap_seconds_path) != leaps_hash:
                raise ValueError("Earth orientation files changed during calculation")
            earth_provenance["iers_prediction_used"] = predicted
            if predicted:
                warnings.append("IERS predicted Earth orientation values were used")
        except CancelledError:
            raise
        except (OSError, ValueError, TypeError, IndexError, RuntimeError) as exc:
            teme_p = teme_v = itrs_p = itrs_v = geo = rotation = None
            warnings.append(f"Earth orientation transform unavailable: {exc}")
    _check_cancel(cancel)
    _notify(progress, 100, "Complete")
    return OrbitResult(
        satellite=snapshot, request=request, times_utc=tuple(_iso_utc(instant) for instant in instants),
        teme_position_km=teme_p, teme_velocity_km_s=teme_v,
        itrs_position_km=itrs_p, itrs_velocity_km_s=itrs_v,
        gcrs_position_km=position, gcrs_velocity_km_s=velocity,
        geodetic_deg_km=geo, earth_rotation=rotation, native_frame="GCRS",
        elapsed_si_seconds=tuple(float(value) for value in seconds),
        warnings=tuple(warnings),
        provenance={
            "earth_data": earth_provenance,
            "integration_timing": {"scale": "elapsed SI seconds from UTC", **timing_provenance},
            "libraries": {name: _package_version(name) for name in ("numpy", "scipy", "astropy", "pyerfa")},
            "app_version": _package_version("orbit-wizard-blue"),
            "method": "DOP853",
            "gravity_model": manual.gravity_model,
            "gravity_approximation": "geocentric fixed GCRS Z axis" if manual.gravity_model == "J2" else "point mass",
            "mu_km3_s2": MU, "earth_reference_radius_km": EARTH_RADIUS_KM, "j2": J2,
            "rtol": _RTOL, "atol_position_km": float(_ATOL[0]), "atol_velocity_km_s": float(_ATOL[3]),
            "max_integration_span_s": _MAX_INTEGRATION_SPAN_S,
            "acceleration": thaw_json(snapshot.source_metadata).get("manual_input", {}).get("acceleration"),
            "geodetic_ellipsoid": "WGS84",
        },
    )
