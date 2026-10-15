"""Offline SGP4 propagation and Earth orientation transformations."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from math import floor
from threading import RLock
from typing import Callable, Iterator

import erfa
import numpy as np
from astropy import units as u
from astropy.coordinates import CartesianDifferential, CartesianRepresentation, GCRS, ITRS, TEME
from astropy.time import Time
from astropy.utils import iers
from sgp4 import omm
from sgp4.api import SGP4_ERRORS, Satrec

from .models import CancelledError, DataSnapshot, EarthData, OrbitRequest, OrbitResult, ValidationError, thaw_json


_EARTH_LOCK = RLock()
_CHUNK = 1024
_MAX_SAMPLES = 100_000
iers.conf.auto_download = False


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


def _check_cancel(cancel: Callable[[], bool] | None) -> None:
    if cancel is not None and cancel():
        raise CancelledError("Orbit calculation cancelled")


def _notify(progress: Callable[[int, str], None] | None, percent: int, message: str) -> None:
    if progress is not None:
        progress(percent, message)


def _time_grid(request: OrbitRequest) -> tuple[datetime, ...]:
    start, end, step = request.start_utc, request.end_utc, request.step_seconds
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        raise ValidationError("Start and end must be datetimes")
    if start.tzinfo is None or end.tzinfo is None or start.utcoffset() is None or end.utcoffset() is None:
        raise ValidationError("Start and end must be timezone-aware")
    if type(step) is not int or step <= 0:
        raise ValidationError("Step must be a positive integer number of seconds")
    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    if end < start:
        raise ValidationError("End must not precede start")
    count = floor((end - start).total_seconds() / step) + 1
    if count > _MAX_SAMPLES:
        raise ValidationError(f"Time grid exceeds {_MAX_SAMPLES} samples")
    return tuple(start + timedelta(seconds=i * step) for i in range(count))


def _satrec(snapshot: DataSnapshot) -> Satrec:
    fields = dict(snapshot.payload)
    for key, value in {"CENTER_NAME": "EARTH", "REF_FRAME": "TEME", "TIME_SYSTEM": "UTC", "MEAN_ELEMENT_THEORY": "SGP4"}.items():
        fields.setdefault(key, value)
        if str(fields[key]).upper() != value:
            raise ValidationError(f"Unsupported {key}: {fields[key]}")
    for key, value in {"MEAN_MOTION_DOT": 0, "MEAN_MOTION_DDOT": 0, "BSTAR": 0, "EPHEMERIS_TYPE": 0, "CLASSIFICATION_TYPE": "U", "ELEMENT_SET_NO": 0, "REV_AT_EPOCH": 0, "OBJECT_ID": ""}.items():
        fields.setdefault(key, value)
    try:
        epoch = datetime.fromisoformat(str(fields["EPOCH"]).replace("Z", "+00:00"))
        if epoch.tzinfo is not None:
            epoch = epoch.astimezone(timezone.utc).replace(tzinfo=None)
        fields["EPOCH"] = epoch.isoformat(timespec="microseconds")
        satellite = Satrec()
        omm.initialize(satellite, fields)
        return satellite
    except (KeyError, ValueError, TypeError, OverflowError) as exc:
        raise ValidationError(f"Invalid CelesTrak GP JSON: {exc}") from exc


def _iso_utc(instant: datetime) -> str:
    return instant.isoformat(timespec="microseconds").replace("+00:00", "Z")


@contextmanager
def _earth_context(earth_data: EarthData) -> Iterator[tuple[iers.IERS_A, iers.LeapSeconds]]:
    """Serialize Astropy/ERFA's process-wide EOP and leap-second state."""
    with _EARTH_LOCK:
        old_leaps = erfa.leap_seconds.get()
        old_download = iers.conf.auto_download
        old_accuracy = iers.conf.iers_degraded_accuracy
        old_iers_leap_url = iers.conf.iers_leap_second_auto_url
        old_ietf_leap_url = iers.conf.ietf_leap_second_auto_url
        try:
            iers.conf.auto_download = False
            iers.conf.iers_degraded_accuracy = "error"
            # Astropy's one-time leap-second check still probes configured URL
            # cache entries with auto_download=False. Remove those URLs here.
            iers.conf.iers_leap_second_auto_url = ""
            iers.conf.ietf_leap_second_auto_url = ""
            if not earth_data.iers_path.is_file() or not earth_data.leap_seconds_path.is_file():
                raise FileNotFoundError("Local IERS or leap-second file is missing")
            # The explicit readers accept local Path objects. Unlike ``open``,
            # they never interpret a source as a URL or consult Astropy's cache.
            table = iers.IERS_A.read(file=earth_data.iers_path)
            try:
                leaps = iers.LeapSeconds.from_iers_leap_seconds(earth_data.leap_seconds_path)
            except ValueError:
                leaps = iers.LeapSeconds.from_leap_seconds_list(earth_data.leap_seconds_path)
            erfa.leap_seconds.set(leaps)
            with iers.earth_orientation_table.set(table):
                yield table, leaps
        finally:
            erfa.leap_seconds.set(old_leaps)
            iers.conf.auto_download = old_download
            iers.conf.iers_degraded_accuracy = old_accuracy
            iers.conf.iers_leap_second_auto_url = old_iers_leap_url
            iers.conf.ietf_leap_second_auto_url = old_ietf_leap_url


def _check_eop_coverage(table: iers.IERS_A, time: Time) -> bool:
    predicted = False
    for label, method in (("UT1-UTC", table.ut1_utc), ("polar motion", table.pm_xy)):
        status = method(time, return_status=True)[-1]
        if np.any(np.asarray(status) < 0):
            raise ValueError(f"IERS {label} data do not cover requested UTC times")
        predicted = predicted or bool(np.any(np.asarray(status) == iers.FROM_IERS_A_PREDICTION))
    return predicted


def _file_sha256(path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _coordinate_chunk(position: np.ndarray, velocity: np.ndarray, time: Time) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    representation = CartesianRepresentation(
        position.T * u.km,
        differentials=CartesianDifferential(velocity.T * u.km / u.s),
    )
    teme = TEME(representation, obstime=time)
    itrs = teme.transform_to(ITRS(obstime=time))
    gcrs = teme.transform_to(GCRS(obstime=time))
    itrs_p = itrs.cartesian.xyz.to_value(u.km).T
    itrs_v = itrs.cartesian.differentials["s"].d_xyz.to_value(u.km / u.s).T
    gcrs_p = gcrs.cartesian.xyz.to_value(u.km).T
    geodetic = itrs.earth_location.geodetic
    geo = np.column_stack((geodetic.lat.to_value(u.deg), geodetic.lon.to_value(u.deg), geodetic.height.to_value(u.km)))
    rotation = np.empty((len(time), 3, 3), dtype=np.float64)
    for axis in range(3):
        basis = np.zeros((3, len(time)), dtype=np.float64)
        basis[axis] = 1.0
        rotated = ITRS(CartesianRepresentation(basis * u.km), obstime=time).transform_to(GCRS(obstime=time))
        rotation[:, :, axis] = rotated.cartesian.xyz.to_value(u.km).T
    return itrs_p, itrs_v, gcrs_p, geo, rotation


def _coordinate_chunk_from_gcrs(
    position: np.ndarray, velocity: np.ndarray, time: Time,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert a numerical GCRS state, including rotating-frame velocity."""
    representation = CartesianRepresentation(
        position.T * u.km,
        differentials=CartesianDifferential(velocity.T * u.km / u.s),
    )
    gcrs = GCRS(representation, obstime=time)
    teme = gcrs.transform_to(TEME(obstime=time))
    itrs = gcrs.transform_to(ITRS(obstime=time))
    teme_p = teme.cartesian.xyz.to_value(u.km).T
    teme_v = teme.cartesian.differentials["s"].d_xyz.to_value(u.km / u.s).T
    itrs_p = itrs.cartesian.xyz.to_value(u.km).T
    itrs_v = itrs.cartesian.differentials["s"].d_xyz.to_value(u.km / u.s).T
    geodetic = itrs.earth_location.geodetic
    geo = np.column_stack((geodetic.lat.to_value(u.deg), geodetic.lon.to_value(u.deg), geodetic.height.to_value(u.km)))
    rotation = np.empty((len(time), 3, 3), dtype=np.float64)
    for axis in range(3):
        basis = np.zeros((3, len(time)), dtype=np.float64)
        basis[axis] = 1.0
        rotated = ITRS(CartesianRepresentation(basis * u.km), obstime=time).transform_to(GCRS(obstime=time))
        rotation[:, :, axis] = rotated.cartesian.xyz.to_value(u.km).T
    return teme_p, teme_v, itrs_p, itrs_v, geo, rotation


def compute_ephemeris(
    snapshot: DataSnapshot,
    request: OrbitRequest,
    earth_data: EarthData | None,
    progress: Callable[[int, str], None] | None = None,
    cancel: Callable[[], bool] | None = None,
) -> OrbitResult:
    """Propagate one GP element set on an inclusive, integer-second UTC grid."""
    _check_cancel(cancel)
    instants = _time_grid(request)
    n = len(instants)
    satellite = _satrec(snapshot)
    _notify(progress, 0, "SGP4 propagation")
    position = np.empty((n, 3), dtype=np.float64)
    velocity = np.empty((n, 3), dtype=np.float64)
    for left in range(0, n, _CHUNK):
        _check_cancel(cancel)
        right = min(left + _CHUNK, n)
        time = Time(instants[left:right], scale="utc")
        errors, p, v = satellite.sgp4_array(np.asarray(time.jd1), np.asarray(time.jd2))
        bad = np.flatnonzero((errors != 0) | ~np.isfinite(p).all(axis=1) | ~np.isfinite(v).all(axis=1))
        if len(bad):
            index = left + int(bad[0])
            code = int(errors[bad[0]])
            raise ValidationError(f"SGP4 failed at {_iso_utc(instants[index])}: {SGP4_ERRORS.get(code, 'non-finite position/velocity')}")
        position[left:right] = p
        velocity[left:right] = v
        _notify(progress, min(50, round(50 * right / n)), "SGP4 propagation")

    warnings: list[str] = []
    if snapshot.warning:
        warnings.append(snapshot.warning)
    if snapshot.stale:
        warnings.append("Satellite source snapshot is stale")
    try:
        epoch = datetime.fromisoformat(str(snapshot.payload["EPOCH"]).replace("Z", "+00:00"))
        if epoch.tzinfo is None:
            epoch = epoch.replace(tzinfo=timezone.utc)
        if max(abs((instant - epoch).total_seconds()) for instant in (instants[0], instants[-1])) > 7 * 86400:
            warnings.append("Orbit exceeds seven days from the element epoch; accuracy is not guaranteed")
    except (KeyError, ValueError):
        pass

    itrs_p = itrs_v = gcrs_p = geo = rotation = None
    earth_provenance = {} if earth_data is None else thaw_json(earth_data.provenance)
    if earth_data is None:
        warnings.append("Earth orientation data are unavailable; ITRS, GCRS, geodetic, and 3D orientation are unavailable")
    else:
        if earth_data.warning:
            warnings.append(earth_data.warning)
        try:
            itrs_p = np.empty((n, 3), dtype=np.float64)
            itrs_v = np.empty((n, 3), dtype=np.float64)
            gcrs_p = np.empty((n, 3), dtype=np.float64)
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
                    time = Time(instants[left:right], scale="utc")
                    predicted = _check_eop_coverage(table, time) or predicted
                    values = _coordinate_chunk(position[left:right], velocity[left:right], time)
                    for label, value, shape in zip(
                        ("ITRS position", "ITRS velocity", "GCRS position", "geodetic coordinates", "Earth rotation"),
                        values,
                        ((right-left, 3),) * 4 + ((right-left, 3, 3),),
                    ):
                        if np.shape(value) != shape or not np.isfinite(value).all():
                            raise ValueError(f"{label} contains invalid shape or non-finite values")
                    for array, value in zip((itrs_p, itrs_v, gcrs_p, geo, rotation), values):
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
            itrs_p = itrs_v = gcrs_p = geo = rotation = None
            warnings.append(f"Earth orientation transform unavailable: {exc}")

    _check_cancel(cancel)
    _notify(progress, 100, "Complete")
    return OrbitResult(
        satellite=snapshot,
        request=request,
        times_utc=tuple(_iso_utc(x) for x in instants),
        teme_position_km=position,
        teme_velocity_km_s=velocity,
        itrs_position_km=itrs_p,
        itrs_velocity_km_s=itrs_v,
        gcrs_position_km=gcrs_p,
        geodetic_deg_km=geo,
        earth_rotation=rotation,
        warnings=tuple(warnings),
        provenance={
            "earth_data": earth_provenance,
            "libraries": {name: _package_version(name) for name in ("sgp4", "numpy", "astropy", "pyerfa")},
            "app_version": _package_version("orbit-wizard-blue"),
            "gravity_model": "WGS72 (sgp4 OMM default)",
            "geodetic_ellipsoid": "WGS84",
        },
    )
