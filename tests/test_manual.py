"""Manual initial conditions and frozen audit snapshots."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import csv
import json

import numpy as np
import pytest

from orbit_wizard_blue.export import export_ephemeris
from orbit_wizard_blue.manual import (
    ConstantAcceleration, KeplerianElements, ManualOrbitInput,
    manual_snapshot, validate_manual_input,
)
from orbit_wizard_blue.models import OrbitRequest, OrbitResult, ValidationError


EPOCH = datetime(2026, 10, 15, tzinfo=timezone.utc)
ELEMENTS = KeplerianElements(7000, 0.01, 45, 20, 30, 40)


def _manual(**changes):
    return replace(ManualOrbitInput("Test craft", EPOCH, elements=ELEMENTS), **changes)


def test_manual_snapshot_captures_full_configuration_and_stable_hash():
    acceleration = ConstantAcceleration((0.001, -0.002, 0.003), "RTN", EPOCH, EPOCH + timedelta(minutes=5))
    value = _manual(gravity_model="two_body", acceleration=acceleration)
    first = manual_snapshot(value)
    second = manual_snapshot(value)
    assert first.sha256 == second.sha256
    assert first.source_url == f"manual://{first.sha256}"
    assert first.source_kind == "manual"
    assert first.source_format == "osculating_elements"
    assert first.payload["NORAD_CAT_ID"] == ""
    assert first.payload["REF_FRAME"] == "GCRS"
    assert first.source_metadata["manual_input"]["acceleration"]["frame"] == "RTN"
    assert first.source_metadata["manual_input"]["gravity_model"] == "two_body"
    assert manual_snapshot(replace(value, name="Other craft")).sha256 != first.sha256
    with pytest.raises((TypeError, FrozenInstanceError)):
        first.source_metadata["manual_input"]["name"] = "Changed"


def test_cartesian_snapshot_and_earth_crossing_elements_starting_above_surface():
    cartesian = ManualOrbitInput("Cartesian", EPOCH, position_km=(7000, 0, 0), velocity_km_s=(0, 7.5, 0))
    assert manual_snapshot(cartesian).source_format == "cartesian_state"
    # This osculating ellipse has a perigee below Earth, but the initial position is above it.
    earth_crossing = _manual(elements=KeplerianElements(7000, 0.2, 0, 0, 0, 180))
    assert validate_manual_input(earth_crossing) is earth_crossing


def test_cartesian_snapshot_round_trips_configuration_and_copies_vectors():
    position = [7000, 0, 0]
    velocity = [0, 7.5, 0]
    thrust = [0.001, 0, 0]
    acceleration = ConstantAcceleration(thrust, "GCRS", EPOCH, EPOCH + timedelta(seconds=10))
    value = ManualOrbitInput("Cartesian", EPOCH, position_km=position, velocity_km_s=velocity,
                             gravity_model="two_body", acceleration=acceleration)
    snapshot = manual_snapshot(value)
    position[0] = 8000
    velocity[1] = 8
    thrust[0] = 0.5
    configuration = snapshot.source_metadata["manual_input"]
    assert configuration["position_km"] == (7000.0, 0.0, 0.0)
    assert configuration["velocity_km_s"] == (0.0, 7.5, 0.0)
    assert configuration["acceleration"]["vector_m_s2"] == (0.001, 0.0, 0.0)
    assert configuration == snapshot.payload["MANUAL_INPUT"]
    assert manual_snapshot(value).sha256 == snapshot.sha256
    assert manual_snapshot(replace(value, velocity_km_s=(0, 7.6, 0))).sha256 != snapshot.sha256
    assert manual_snapshot(replace(value, gravity_model="J2")).sha256 != snapshot.sha256
    with pytest.raises(FrozenInstanceError):
        value.velocity_km_s = (0, 8, 0)


@pytest.mark.parametrize("changes", [
    {"elements": KeplerianElements(7000, 1, 0, 0, 0, 0)},
    {"elements": KeplerianElements(7000, -0.1, 0, 0, 0, 0)},
    {"elements": KeplerianElements(7000, 0, 181, 0, 0, 0)},
    {"elements": KeplerianElements(7000, 0, 0, 360, 0, 0)},
    {"elements": KeplerianElements(7000, 0, 0, 0, float("nan"), 0)},
    {"elements": KeplerianElements(7000, 0, 0, 0, 0, True)},
    {"elements": KeplerianElements("7000", 0, 0, 0, 0, 0)},
    {"elements": KeplerianElements(7000, 0.2, 0, 0, 0, 0)},
    {"gravity_model": "unknown"},
    {"epoch_utc": EPOCH.replace(tzinfo=None)},
    {"epoch_utc": EPOCH.astimezone(timezone(timedelta(hours=9)))},
])
def test_invalid_element_inputs_rejected(changes):
    with pytest.raises(ValidationError):
        validate_manual_input(_manual(**changes))


@pytest.mark.parametrize("position,velocity", [
    ((6378, 0, 0), (0, 7.5, 0)),
    ((7000, 0, 0), (0, 12, 0)),
    ((7000, 0, 0), (1, 0, 0)),
    ((7000, float("inf"), 0), (0, 7.5, 0)),
    ((1e308, 1e308, 0), (0, 7.5, 0)),
    ((7000, 0, 0), (0, 1e308, 0)),
    ((1e200, 0, 0), (0, 1e100, 0)),
])
def test_invalid_cartesian_state_rejected(position, velocity):
    with pytest.raises(ValidationError):
        validate_manual_input(_manual(elements=None, position_km=position, velocity_km_s=velocity))


@pytest.mark.parametrize("acceleration", [
    ConstantAcceleration((0, 0, 0), "BODY", EPOCH, EPOCH + timedelta(seconds=1)),
    ConstantAcceleration((float("nan"), 0, 0), "GCRS", EPOCH, EPOCH + timedelta(seconds=1)),
    ConstantAcceleration((0, 0, 0), "RTN", EPOCH - timedelta(seconds=1), EPOCH),
    ConstantAcceleration((0, 0, 0), "RTN", EPOCH + timedelta(seconds=1), EPOCH),
])
def test_invalid_acceleration_rejected(acceleration):
    with pytest.raises(ValidationError):
        validate_manual_input(_manual(acceleration=acceleration))


def test_gcrs_native_result_exports_velocity_and_blank_teme(tmp_path):
    snapshot = manual_snapshot(_manual())
    request = OrbitRequest(EPOCH, EPOCH)
    result = OrbitResult(
        snapshot, request, ("2026-10-15T00:00:00.000000Z",), None, None,
        None, None, np.array([[7000., 0., 0.]]), None, None,
        provenance={"integrator": {"gravity_model": "J2"}},
        gcrs_velocity_km_s=np.array([[0., 7.5, 0.]]), native_frame="GCRS",
    )
    csv_path, json_path = export_ephemeris(result, tmp_path / "manual.csv")
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["norad_id"] == ""
    assert row["teme_x_km"] == row["teme_vx_km_s"] == ""
    assert row["gcrs_x_km"] == "7000.0"
    assert row["gcrs_vy_km_s"] == "7.5"
    metadata = json.loads(json_path.read_text(encoding="utf-8"))
    assert metadata["schema_version"] == 3
    assert metadata["native_frame"] == "GCRS"
    assert metadata["frames_available"]["TEME"] is False
    assert metadata["source"]["metadata"]["manual_input"]["elements"]["a_km"] == 7000
    assert metadata["provenance"]["integrator"]["gravity_model"] == "J2"
    with pytest.raises(ValueError):
        result.gcrs_velocity_km_s[0, 0] = 1
    with pytest.raises(ValidationError, match="GCRS native"):
        replace(result, gcrs_velocity_km_s=None)
