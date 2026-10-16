"""Numerical behavior and failure boundaries for ephemeris computation."""

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
import erfa
from astropy import units as u
from astropy.time import Time
from astropy.utils import iers

from orbit_wizard_blue.models import CancelledError, DataSnapshot, EarthData, OrbitRequest, ValidationError, thaw_json
from orbit_wizard_blue.orbit import _check_eop_coverage, _coordinate_chunk, compute_ephemeris


FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "vallado_00005.json").read_text())
EPOCH = datetime.fromisoformat(FIXTURE["elements"]["EPOCH"]).replace(tzinfo=timezone.utc)


def snapshot():
    return DataSnapshot(dict(FIXTURE["elements"]), FIXTURE["source_url"], "2000-06-27T00:00:00Z", "2000-06-27T00:00:00Z", "abc")


def earth():
    return EarthData(Path(iers.IERS_A_FILE), Path(iers.IERS_LEAP_SECOND_FILE), {"iers": "astropy bundled", "leaps": "astropy bundled"})


def test_vallado_reference_vector_and_immutable_snapshot():
    source = snapshot()
    request = OrbitRequest(EPOCH, EPOCH)
    result = compute_ephemeris(source, request, None)
    np.testing.assert_allclose(result.teme_position_km[0], FIXTURE["teme_at_epoch_km"], atol=0.03)
    np.testing.assert_allclose(result.teme_velocity_km_s[0], FIXTURE["teme_velocity_at_epoch_km_s"], atol=3e-5)
    assert result.itrs_position_km is None
    with pytest.raises(ValueError):
        result.teme_position_km[0, 0] = 0
    with pytest.raises(ValueError):
        result.teme_position_km.setflags(write=True)
    with pytest.raises(TypeError):
        source.payload["MEAN_MOTION"] = 0
    assert result.satellite.payload["MEAN_MOTION"] == FIXTURE["elements"]["MEAN_MOTION"]


def test_nested_metadata_is_frozen_and_can_be_thawed():
    payload = dict(FIXTURE["elements"])
    payload["nested"] = [{"number": 1}]
    source_metadata = {"origin": {"tags": ["validated"]}}
    satellite = DataSnapshot(payload, "local", "fetch", "check", "hash", source_metadata=source_metadata)
    payload["nested"][0]["number"] = 2
    source_metadata["origin"]["tags"].append("later")
    assert satellite.payload["nested"][0]["number"] == 1
    assert satellite.source_metadata["origin"]["tags"] == ("validated",)
    with pytest.raises(TypeError):
        satellite.payload["nested"][0]["number"] = 3
    with pytest.raises(TypeError):
        satellite.source_metadata["origin"]["tags"] = ()
    result = compute_ephemeris(satellite, OrbitRequest(EPOCH, EPOCH), None)
    with pytest.raises(TypeError):
        result.provenance["libraries"]["sgp4"] = "changed"
    assert thaw_json(satellite.source_metadata) == {"origin": {"tags": ["validated"]}}


def test_utc_grid_includes_only_exact_steps_and_limit():
    result = compute_ephemeris(snapshot(), OrbitRequest(EPOCH, EPOCH + timedelta(seconds=125), 60), None)
    assert result.times_utc == tuple((EPOCH + timedelta(seconds=n)).isoformat(timespec="microseconds").replace("+00:00", "Z") for n in (0, 60, 120))
    assert result.elapsed_si_seconds == (0.0, 60.0, 120.0)
    with pytest.raises(ValidationError, match="100000"):
        compute_ephemeris(snapshot(), OrbitRequest(EPOCH, EPOCH + timedelta(seconds=100000), 1), None)
    with pytest.raises(ValidationError, match="positive integer"):
        compute_ephemeris(snapshot(), OrbitRequest(EPOCH, EPOCH, 0), None)


def test_playback_elapsed_seconds_use_selected_leap_table(tmp_path):
    epoch = datetime(2016, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    fields = dict(FIXTURE["elements"], EPOCH="2016-12-31T23:59:59")
    source = DataSnapshot(fields, "test", "fetch", "check", "hash")
    request = OrbitRequest(epoch, epoch + timedelta(seconds=2), 1)
    bundled = compute_ephemeris(source, request, None)
    assert bundled.elapsed_si_seconds == (0.0, 2.0, 3.0)

    # A valid supplied table without the 2017 leap must change the elapsed clock.
    leap_path = tmp_path / "leaps.dat"
    lines = Path(iers.IERS_LEAP_SECOND_FILE).read_text().splitlines()
    leap_path.write_text("\n".join(line for line in lines if not line.lstrip().startswith("57754.0")) + "\n")
    supplied = EarthData(Path(iers.IERS_A_FILE), leap_path, {})
    altered = compute_ephemeris(source, request, supplied)
    assert altered.elapsed_si_seconds == (0.0, 1.0, 2.0)

    missing = EarthData(Path(iers.IERS_A_FILE), tmp_path / "missing", {})
    fallback = compute_ephemeris(source, request, missing)
    assert fallback.elapsed_si_seconds == bundled.elapsed_si_seconds


def test_elapsed_seconds_are_immutable_and_ordered():
    result = compute_ephemeris(snapshot(), OrbitRequest(EPOCH, EPOCH + timedelta(seconds=120), 60), None)
    values = [0.0, 60.0, 120.0]
    copy = replace(result, elapsed_si_seconds=values)
    values[1] = 999.0
    assert copy.elapsed_si_seconds == (0.0, 60.0, 120.0)
    with pytest.raises(ValidationError, match="Elapsed SI seconds"):
        replace(result, elapsed_si_seconds=(0.0, 60.0, 60.0))
    with pytest.raises(ValidationError, match="Elapsed SI seconds"):
        replace(result, elapsed_si_seconds=(0.0, float("nan"), 120.0))


def test_cancel_before_and_during_propagation():
    with pytest.raises(CancelledError):
        compute_ephemeris(snapshot(), OrbitRequest(EPOCH, EPOCH), None, cancel=lambda: True)
    calls = []
    with pytest.raises(CancelledError):
        compute_ephemeris(snapshot(), OrbitRequest(EPOCH, EPOCH + timedelta(seconds=5000), 1), None,
                          progress=lambda n, _: calls.append(n), cancel=lambda: bool(calls))


def test_itrs_velocity_and_earth_rotation_are_coherent():
    result = compute_ephemeris(snapshot(), OrbitRequest(EPOCH, EPOCH + timedelta(seconds=2), 1), earth())
    assert result.itrs_position_km is not None, result.warnings
    assert result.gcrs_position_km is not None
    np.testing.assert_allclose(result.earth_rotation @ result.itrs_position_km[..., None],
                               result.gcrs_position_km[..., None], atol=1e-5)
    finite_difference = (result.itrs_position_km[2] - result.itrs_position_km[0]) / 2
    np.testing.assert_allclose(result.itrs_velocity_km_s[1], finite_difference, atol=0.005)
    assert np.all(result.geodetic_deg_km[:, 2] > 0)


def test_vallado_teme_to_pef_position_with_fixed_eop():
    # Vallado et al. Appendix C gives both TEME and PEF coordinates for this
    # instant and UT1/polar-motion values. Undo polar motion to compare PEF.
    time = Time(["2000-06-28T15:08:51.655"], scale="utc")
    time.delta_ut1_utc = 0.162360
    table = iers.IERS_A.open(str(iers.IERS_A_FILE)).copy()
    table["PM_x"][:] = 0.0987 * u.arcsec
    table["PM_y"][:] = 0.286 * u.arcsec
    position = np.array([[3961.0035498, 6010.7511740, 4619.3009301]])
    velocity = np.array([[-5.315109069, 3.963813071, 1.752758562]])
    with iers.earth_orientation_table.set(table):
        itrs_position = _coordinate_chunk(position, velocity, time)[0][0]
    arcsec_to_rad = np.pi / 648000
    polar = erfa.pom00(0.0987 * arcsec_to_rad, 0.286 * arcsec_to_rad, 0)
    pef_position = polar.T @ itrs_position
    np.testing.assert_allclose(pef_position, [298.8036328, -7192.3146229, 4619.3015310], atol=0.002)


def test_iers_coverage_is_explicit_and_teme_survives_unusable_earth_data(tmp_path):
    table = iers.IERS_A.open(str(iers.IERS_A_FILE))
    with pytest.raises(ValueError, match="do not cover"):
        _check_eop_coverage(table, Time("1965-01-01T00:00:00", scale="utc"))
    missing = EarthData(tmp_path / "missing-eop", tmp_path / "missing-leaps", {})
    result = compute_ephemeris(snapshot(), OrbitRequest(EPOCH, EPOCH), missing)
    assert result.itrs_position_km is None
    assert any("unavailable" in warning for warning in result.warnings)


@pytest.mark.parametrize("invalid_value", [float("nan"), float("inf")])
def test_nonfinite_coordinate_output_keeps_only_valid_teme(monkeypatch, invalid_value):
    from orbit_wizard_blue import orbit as module

    def broken_coordinate_chunk(position, velocity, time):
        vectors = [np.zeros((len(time), 3)) for _ in range(4)]
        vectors[0][0, 0] = invalid_value
        return (*vectors, np.broadcast_to(np.eye(3), (len(time), 3, 3)))

    monkeypatch.setattr(module, "_coordinate_chunk", broken_coordinate_chunk)
    result = compute_ephemeris(snapshot(), OrbitRequest(EPOCH, EPOCH), earth())
    assert np.isfinite(result.teme_position_km).all()
    assert result.itrs_position_km is None
    assert result.gcrs_position_km is None
    assert result.earth_rotation is None
    assert any("non-finite" in warning for warning in result.warnings)


@pytest.mark.parametrize("mean_motion, altitude_band_km", [
    (15.5, (150, 700)),
    (2.0, (10_000, 30_000)),
    (1.0027, (30_000, 40_000)),
])
def test_leo_meo_geo_and_extended_catalog_id(mean_motion, altitude_band_km):
    fields = dict(FIXTURE["elements"])
    fields.update({"NORAD_CAT_ID": 100001, "EPOCH": "2025-01-02T00:00:00", "MEAN_MOTION": mean_motion,
                   "ECCENTRICITY": 0.0001, "BSTAR": 0})
    instant = datetime(2025, 1, 2, tzinfo=timezone.utc)
    source = DataSnapshot(fields, "test", "2025-01-02T00:00:00Z", "2025-01-02T00:00:00Z", "hash")
    result = compute_ephemeris(source, OrbitRequest(instant, instant), earth())
    assert result.itrs_position_km is not None, result.warnings
    assert altitude_band_km[0] < result.geodetic_deg_km[0, 2] < altitude_band_km[1]
    assert result.satellite.payload["NORAD_CAT_ID"] == 100001
