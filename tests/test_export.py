"""Export fidelity and partial write recovery."""

import csv
import json
from datetime import datetime, timezone

import numpy as np
import pytest

from orbit_wizard_blue.export import export_ephemeris
from orbit_wizard_blue.models import DataSnapshot, OrbitRequest, OrbitResult


def result():
    now = datetime(2026, 1, 2, tzinfo=timezone.utc)
    return OrbitResult(
        satellite=DataSnapshot({"OBJECT_NAME": "Test Satellite", "NORAD_CAT_ID": 12345, "EPOCH": "2026-01-02T00:00:00"}, "https://example.test/gp", "fetch", "check", "hash"),
        request=OrbitRequest(now, now), times_utc=("2026-01-02T00:00:00.000000Z",),
        teme_position_km=np.array([[1., 2., 3.]]), teme_velocity_km_s=np.array([[4., 5., 6.]]),
        itrs_position_km=None, itrs_velocity_km_s=None, gcrs_position_km=None,
        geodetic_deg_km=None, earth_rotation=None, warnings=("No EOP",),
        provenance={"earth_data": {"iers_sha256": "fixed-hash"}, "libraries": {"sgp4": "test"}},
    )


def test_csv_bom_and_companion_metadata_match_result(tmp_path):
    csv_path, json_path = export_ephemeris(result(), tmp_path / "orbit.csv")
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        records = list(csv.DictReader(stream))
    assert records[0]["sample_index"] == "0"
    assert records[0]["satellite_name"] == "Test Satellite"
    assert records[0]["norad_id"] == "12345"
    assert records[0]["teme_x_km"] == "1.0"
    assert records[0]["itrs_x_km"] == ""
    metadata = json.loads(json_path.read_text(encoding="utf-8"))
    assert metadata["source"]["payload"]["NORAD_CAT_ID"] == 12345
    assert metadata["source"]["sha256"] == "hash"
    assert metadata["request"]["step_seconds"] == 60
    assert metadata["provenance"]["earth_data"]["iers_sha256"] == "fixed-hash"


def test_failed_second_replace_restores_existing_pair(tmp_path, monkeypatch):
    from orbit_wizard_blue import export as module

    csv_path = tmp_path / "orbit.csv"
    json_path = tmp_path / "orbit.json"
    csv_path.write_text("old csv")
    json_path.write_text("old json")
    actual_replace = module.os.replace
    count = 0

    def fail_second(source, destination):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("simulated failure")
        return actual_replace(source, destination)

    monkeypatch.setattr(module.os, "replace", fail_second)
    with pytest.raises(OSError, match="simulated"):
        export_ephemeris(result(), csv_path)
    assert csv_path.read_text() == "old csv"
    assert json_path.read_text() == "old json"
