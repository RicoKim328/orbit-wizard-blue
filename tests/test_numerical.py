"""Independent physical checks for manual GCRS propagation."""

from datetime import datetime, timedelta, timezone
from math import pi, sqrt
from pathlib import Path
from shutil import copyfile

import numpy as np
import pytest
from astropy.utils import iers

from orbit_wizard_blue.manual import (
    EARTH_RADIUS_KM, MU, ConstantAcceleration, KeplerianElements, ManualOrbitInput,
)
from orbit_wizard_blue.models import CancelledError, EarthData, OrbitRequest, ValidationError
from orbit_wizard_blue.numerical import compute_manual_ephemeris, elements_to_state


EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)
RADIUS = 7000.0
CIRCULAR_SPEED = sqrt(MU / RADIUS)


def _manual(**changes):
    values = dict(name="Manual Test", epoch_utc=EPOCH, position_km=(RADIUS, 0, 0),
                  velocity_km_s=(0, CIRCULAR_SPEED, 0), gravity_model="two_body")
    values.update(changes)
    return ManualOrbitInput(**values)


def _request(seconds=600, step=60):
    return OrbitRequest(EPOCH, EPOCH + timedelta(seconds=seconds), step)


def test_two_body_matches_analytic_circular_orbit_and_conserves_energy():
    duration = 2 * pi * sqrt(RADIUS**3 / MU)
    result = compute_manual_ephemeris(_manual(), _request(round(duration), 30), None)
    times = np.arange(len(result.times_utc)) * 30.0
    phase = sqrt(MU / RADIUS**3) * times
    expected_position = RADIUS * np.column_stack((np.cos(phase), np.sin(phase), np.zeros_like(phase)))
    expected_velocity = CIRCULAR_SPEED * np.column_stack((-np.sin(phase), np.cos(phase), np.zeros_like(phase)))
    np.testing.assert_allclose(result.gcrs_position_km, expected_position, atol=1e-4)
    np.testing.assert_allclose(result.gcrs_velocity_km_s, expected_velocity, atol=1e-7)
    energy = np.sum(result.gcrs_velocity_km_s**2, axis=1) / 2 - MU / np.linalg.norm(result.gcrs_position_km, axis=1)
    assert np.ptp(energy) < 1e-8
    assert result.native_frame == "GCRS"
    assert result.teme_position_km is None
    assert result.itrs_position_km is None
    assert result.provenance["method"] == "DOP853"


def test_elements_and_cartesian_initial_states_match():
    elements = KeplerianElements(RADIUS, 0, 0, 0, 0, 0)
    position, velocity = elements_to_state(elements)
    np.testing.assert_allclose(position, (RADIUS, 0, 0), atol=1e-12)
    np.testing.assert_allclose(velocity, (0, CIRCULAR_SPEED, 0), atol=1e-12)
    element_input = ManualOrbitInput("Manual Test", EPOCH, elements=elements, gravity_model="two_body")
    from_elements = compute_manual_ephemeris(element_input, _request(), None)
    from_state = compute_manual_ephemeris(_manual(), _request(), None)
    np.testing.assert_allclose(from_elements.gcrs_position_km, from_state.gcrs_position_km, atol=1e-9)
    np.testing.assert_allclose(from_elements.gcrs_velocity_km_s, from_state.gcrs_velocity_km_s, atol=1e-12)

    inclined = KeplerianElements(10000, 0.1, 90, 90, 0, 0)
    position, velocity = elements_to_state(inclined)
    np.testing.assert_allclose(position, (0, 9000, 0), atol=1e-10)
    np.testing.assert_allclose(velocity, (0, 0, sqrt(MU / 9900) * 1.1), atol=1e-12)


def test_j2_causes_expected_retrograde_node_drift():
    # Secular J2 node rate: -3/2 J2 n (Re/a)^2 cos(i) for a near-circular orbit.
    inclination = 45.0
    elements = KeplerianElements(RADIUS, 0.001, inclination, 30, 0, 0)
    manual = ManualOrbitInput("Inclined", EPOCH, elements=elements, gravity_model="J2")
    result = compute_manual_ephemeris(manual, _request(86400, 3600), None)
    h0 = np.cross(result.gcrs_position_km[0], result.gcrs_velocity_km_s[0])
    h1 = np.cross(result.gcrs_position_km[-1], result.gcrs_velocity_km_s[-1])
    node0 = np.arctan2(h0[0], -h0[1])
    node1 = np.arctan2(h1[0], -h1[1])
    drift = (node1 - node0 + pi) % (2 * pi) - pi
    predicted = -1.5 * 1.08262668e-3 * sqrt(MU / RADIUS**3) * (EARTH_RADIUS_KM / RADIUS)**2 * np.cos(np.deg2rad(inclination)) * 86400
    assert drift < 0
    assert abs(drift - predicted) < np.deg2rad(0.2)
    assert result.provenance["gravity_approximation"] == "geocentric fixed GCRS Z axis"


def test_acceleration_frames_and_boundaries():
    baseline = compute_manual_ephemeris(_manual(), _request(180, 30), None)
    burn = ConstantAcceleration((0.0, 10.0, 0.0), "GCRS", EPOCH + timedelta(seconds=60), EPOCH + timedelta(seconds=120))
    powered = compute_manual_ephemeris(_manual(acceleration=burn), _request(180, 30), None)
    np.testing.assert_allclose(powered.gcrs_position_km[:3], baseline.gcrs_position_km[:3], atol=1e-9)
    assert np.linalg.norm(powered.gcrs_velocity_km_s[4] - baseline.gcrs_velocity_km_s[4]) > 5e-4
    assert powered.provenance["acceleration"]["frame"] == "GCRS"

    zero = ConstantAcceleration((0, 0, 0), "RTN", EPOCH, EPOCH + timedelta(seconds=120))
    zero_result = compute_manual_ephemeris(_manual(acceleration=zero), _request(180, 30), None)
    np.testing.assert_allclose(zero_result.gcrs_position_km, baseline.gcrs_position_km, atol=1e-8)
    radial = ConstantAcceleration((10, 0, 0), "RTN", EPOCH, EPOCH + timedelta(seconds=30))
    radial_result = compute_manual_ephemeris(_manual(acceleration=radial), _request(180, 30), None)
    assert radial_result.gcrs_velocity_km_s[1, 0] > baseline.gcrs_velocity_km_s[1, 0]


def test_gcrs_constant_force_has_exact_units_and_start_stop(monkeypatch):
    # A zero-gravity reference gives an analytic coast, burn, coast trajectory.
    monkeypatch.setattr("orbit_wizard_blue.numerical.MU", 0.0)
    burn = ConstantAcceleration((0.0, 10.0, 0.0), "GCRS", EPOCH + timedelta(seconds=60), EPOCH + timedelta(seconds=120))
    result = compute_manual_ephemeris(_manual(acceleration=burn), _request(180, 30), None)
    for index, time in enumerate(range(0, 181, 30)):
        burn_time = min(max(time - 60, 0), 60)
        coast_after = max(time - 120, 0)
        expected_y = CIRCULAR_SPEED * time + 0.5 * 0.01 * burn_time**2 + 0.01 * 60 * coast_after
        expected_vy = CIRCULAR_SPEED + 0.01 * burn_time
        np.testing.assert_allclose(result.gcrs_position_km[index], (RADIUS, expected_y, 0), atol=1e-8)
        np.testing.assert_allclose(result.gcrs_velocity_km_s[index], (0, expected_vy, 0), atol=1e-10)


def test_impact_detected_past_last_sample_and_cancellation_inside_rhs():
    descending = _manual(velocity_km_s=(0, 6.0, 0))
    with pytest.raises(ValidationError, match="intersects the Earth"):
        compute_manual_ephemeris(descending, _request(4000, 5000), None)

    # Both output positions are above the surface; an interior periapsis dips 1 m below it.
    shallow = ManualOrbitInput(
        "Shallow impact", EPOCH,
        elements=KeplerianElements(7000, 1 - (EARTH_RADIUS_KM - 0.001) / 7000, 0, 0, 0, 180),
        gravity_model="two_body",
    )
    with pytest.raises(ValidationError, match="intersects the Earth"):
        compute_manual_ephemeris(shallow, _request(6000, 6000), None)

    calls = 0

    def cancel():
        nonlocal calls
        calls += 1
        return calls > 2

    with pytest.raises(CancelledError):
        compute_manual_ephemeris(_manual(), _request(86400), None, cancel=cancel)
    assert calls == 3


def test_eop_transform_and_missing_data_fallback():
    earth = EarthData(iers.IERS_A_FILE, iers.IERS_LEAP_SECOND_FILE, {"kind": "bundled"})
    result = compute_manual_ephemeris(_manual(), _request(2, 1), earth)
    assert result.teme_position_km is not None
    assert result.itrs_position_km is not None
    assert result.earth_rotation is not None
    np.testing.assert_allclose(
        np.einsum("nij,nj->ni", result.earth_rotation, result.itrs_position_km),
        result.gcrs_position_km, atol=0.1,
    )
    assert result.gcrs_velocity_km_s.shape == (3, 3)
    np.testing.assert_allclose(
        (result.itrs_position_km[2] - result.itrs_position_km[0]) / 2,
        result.itrs_velocity_km_s[1], atol=3e-5,
    )

    missing = EarthData("/missing/iers", "/missing/leaps", {"kind": "missing"})
    fallback = compute_manual_ephemeris(_manual(), _request(120, 60), missing)
    assert fallback.gcrs_position_km is not None
    assert fallback.teme_position_km is None
    assert fallback.itrs_position_km is None
    assert any("Earth orientation transform unavailable" in warning for warning in fallback.warnings)


def test_epoch_and_grid_validation():
    with pytest.raises(ValidationError, match="initial-state epoch"):
        compute_manual_ephemeris(_manual(), OrbitRequest(EPOCH + timedelta(seconds=1), EPOCH + timedelta(seconds=10), 1), None)
    with pytest.raises(ValidationError, match="100000"):
        compute_manual_ephemeris(_manual(), _request(100000, 1), None)


def test_leap_second_is_counted_in_integration_elapsed_time():
    epoch = datetime(2016, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    manual = ManualOrbitInput("Leap second", epoch, position_km=(RADIUS, 0, 0),
                              velocity_km_s=(0, CIRCULAR_SPEED, 0), gravity_model="two_body")
    result = compute_manual_ephemeris(manual, OrbitRequest(epoch, epoch + timedelta(seconds=2), 1), None)
    # The datetime grid omits the :60 label, so 00:00:00 is two physical seconds after 23:59:59.
    angular_rate = sqrt(MU / RADIUS**3)
    assert result.times_utc[1] == "2017-01-01T00:00:00.000000Z"
    assert result.elapsed_si_seconds == (0.0, 2.0, 3.0)
    assert result.gcrs_position_km[1, 1] == pytest.approx(RADIUS * np.sin(2 * angular_rate), abs=1e-6)
    assert result.gcrs_position_km[2, 1] == pytest.approx(RADIUS * np.sin(3 * angular_rate), abs=1e-6)


def test_expired_bundled_leap_table_warns_for_native_only_result():
    future = datetime(2030, 1, 1, tzinfo=timezone.utc)
    manual = ManualOrbitInput("Future", future, position_km=(RADIUS, 0, 0),
                              velocity_km_s=(0, CIRCULAR_SPEED, 0), gravity_model="two_body")
    result = compute_manual_ephemeris(manual, OrbitRequest(future, future + timedelta(seconds=60), 60), None)
    assert result.gcrs_position_km is not None
    assert any("numerical timing has expired" in warning for warning in result.warnings)
    assert result.provenance["integration_timing"]["leap_seconds_expires"]


def test_leap_file_change_during_timing_uses_stable_bundle(monkeypatch, tmp_path):
    import orbit_wizard_blue.numerical as numerical

    copied = tmp_path / "leap-seconds.list"
    copyfile(iers.IERS_LEAP_SECOND_FILE, copied)
    supplied = EarthData(iers.IERS_A_FILE, copied, {"kind": "cache"})
    original_hash = numerical._file_sha256
    reads = 0

    def changed_hash(path):
        nonlocal reads
        if Path(path) == copied:
            reads += 1
            if reads <= 2:
                return "before" if reads == 1 else "after"
        return original_hash(path)

    monkeypatch.setattr(numerical, "_file_sha256", changed_hash)
    result = compute_manual_ephemeris(_manual(), _request(60, 60), supplied)
    assert reads >= 2
    assert result.provenance["integration_timing"]["leap_seconds_file_sha256_used"] == original_hash(
        Path(iers.IERS_LEAP_SECOND_FILE)
    )
    assert any("bundled table used" in warning and "changed" in warning for warning in result.warnings)
