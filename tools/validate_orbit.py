"""Reproducible offline orbit fixture and 100,000-sample validation.

Run from the project root with ``.venv/bin/python tools/validate_orbit.py``.
``build_fixture()`` can also supply a small, deterministic GUI demonstration.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import socket
import sys
from time import perf_counter

import numpy as np
from astropy.utils import iers

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orbit_wizard_blue.models import CancelledError, DataSnapshot, EarthData, OrbitRequest
from orbit_wizard_blue.orbit import compute_ephemeris


EPOCH = datetime(2019, 1, 1, tzinfo=timezone.utc)


def build_fixture(orbit: str = "meo", count: int = 181) -> tuple[DataSnapshot, OrbitRequest, EarthData]:
    """Return deterministic local GP/IERS inputs; perform no data fetch."""
    if orbit not in ("meo", "geo") or not 1 <= count <= 100_000:
        raise ValueError("orbit must be meo/geo and count must be 1..100000")
    mean_motion = 2.0 if orbit == "meo" else 1.0027
    payload = {
        "OBJECT_NAME": f"VALIDATION {orbit.upper()}",
        "OBJECT_ID": "2019-001A",
        "NORAD_CAT_ID": 100001 if orbit == "meo" else 100002,
        "EPOCH": "2019-01-01T00:00:00.000000",
        "MEAN_MOTION": mean_motion,
        "ECCENTRICITY": 0.001,
        "INCLINATION": 55.0 if orbit == "meo" else 0.2,
        "RA_OF_ASC_NODE": 40.0,
        "ARG_OF_PERICENTER": 30.0,
        "MEAN_ANOMALY": 20.0,
        "BSTAR": 0.0,
        "MEAN_MOTION_DOT": 0.0,
        "MEAN_MOTION_DDOT": 0.0,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    snapshot = DataSnapshot(payload, "fixture://orbit-validation", "2019-01-01T00:00:00Z",
                            "2019-01-01T00:00:00Z", sha256(canonical).hexdigest())
    request = OrbitRequest(EPOCH, EPOCH + timedelta(seconds=count - 1), 1)
    earth = EarthData(Path(iers.IERS_A_FILE), Path(iers.IERS_LEAP_SECOND_FILE),
                      {"source": "astropy-iers-data package", "validation_fixture": orbit})
    return snapshot, request, earth


def validate(orbit: str, count: int) -> dict[str, object]:
    snapshot, request, earth = build_fixture(orbit, count)
    # A network attempt during calculation is a validation failure.
    original_connect = socket.socket.connect

    def block_network(self, address):
        raise RuntimeError(f"Unexpected network access during calculation: {address}")

    socket.socket.connect = block_network
    try:
        started = perf_counter()
        result = compute_ephemeris(snapshot, request, earth)
        elapsed = perf_counter() - started
        cancellation_seconds = {}
        for phase, threshold in (("propagation", 2), ("conversion", 51)):
            cancel_started = perf_counter()
            progress = [0]

            def on_progress(percent: int, message: str) -> None:
                progress[0] = percent

            try:
                compute_ephemeris(snapshot, request, earth, progress=on_progress,
                                  cancel=lambda: progress[0] >= threshold)
            except CancelledError:
                cancellation_seconds[phase] = round(perf_counter() - cancel_started, 3)
            else:
                raise AssertionError(f"Cancellation was not honored during {phase}")
    finally:
        socket.socket.connect = original_connect
    arrays = {
        "teme_position": result.teme_position_km,
        "teme_velocity": result.teme_velocity_km_s,
        "itrs_position": result.itrs_position_km,
        "itrs_velocity": result.itrs_velocity_km_s,
        "gcrs_position": result.gcrs_position_km,
        "geodetic": result.geodetic_deg_km,
        "earth_rotation": result.earth_rotation,
    }
    for name, array in arrays.items():
        if array is None or len(array) != count or not np.isfinite(array).all():
            raise AssertionError(f"{name} is missing, incorrectly sized, or non-finite")
    selected = np.array([0, count // 2, count - 1])
    rotated = np.einsum("nij,nj->ni", result.earth_rotation[selected], result.itrs_position_km[selected])
    np.testing.assert_allclose(rotated, result.gcrs_position_km[selected], atol=1e-5)
    try:
        import resource

        peak_rss_mib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except ImportError:
        peak_rss_mib = None
    return {
        "orbit": orbit,
        "samples": count,
        "seconds": round(elapsed, 3),
        "peak_rss_mib": None if peak_rss_mib is None else round(peak_rss_mib, 1),
        "cancellation_seconds": cancellation_seconds,
        "all_arrays_finite": True,
        "first_utc": result.times_utc[0],
        "last_utc": result.times_utc[-1],
        "warnings": result.warnings,
        "iers_sha256_used": result.provenance["earth_data"]["iers_file_sha256_used"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orbit", choices=("meo", "geo"), default="meo")
    parser.add_argument("--count", type=int, default=100_000)
    options = parser.parse_args()
    print(json.dumps(validate(options.orbit, options.count), ensure_ascii=False, indent=2))
