"""Offline integration of source snapshots, propagation, and audited export."""

from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
from urllib.error import URLError

from orbit_wizard_blue.data import DataService
from orbit_wizard_blue.export import export_ephemeris
from orbit_wizard_blue.models import OrbitRequest
from orbit_wizard_blue.orbit import compute_ephemeris


_GP = {
    "OBJECT_NAME": "ISS (ZARYA)",
    "NORAD_CAT_ID": 25544,
    "EPOCH": "2026-10-15T00:00:00.000000",
    "MEAN_MOTION": 15.5,
    "ECCENTRICITY": 0.0005,
    "INCLINATION": 51.6,
    "RA_OF_ASC_NODE": 20.0,
    "ARG_OF_PERICENTER": 30.0,
    "MEAN_ANOMALY": 40.0,
}


class _Response:
    status = 200
    headers = {}

    def __init__(self, payload):
        self._stream = BytesIO(payload)

    def read(self, size=-1):
        return self._stream.read(size)

    def close(self):
        self._stream.close()


def test_source_refresh_does_not_change_existing_result_or_export(tmp_path):
    clock = [datetime(2026, 10, 15, tzinfo=timezone.utc)]
    gp_requests = []
    earth_requests = []

    def opener(request, timeout):
        if "gp.php" in request.full_url:
            gp_requests.append(request.full_url)
            fields = dict(_GP)
            if len(gp_requests) == 2:
                fields["MEAN_MOTION"] = 15.6
                fields["EPOCH"] = "2026-10-15T01:00:00.000000"
            return _Response(json.dumps([fields]).encode())
        earth_requests.append(request.full_url)
        raise URLError("offline test")

    service = DataService(tmp_path / "cache", opener=opener, clock=lambda: clock[0])
    source = service.get_satellite("25544")
    earth = service.get_earth_data()
    assert earth.provenance["iers"]["kind"] == "bundled"
    assert earth.provenance["leap_seconds"]["kind"] == "bundled"
    assert len(earth_requests) == 2

    request = OrbitRequest(clock[0], clock[0] + timedelta(minutes=2), 60)
    first_result = compute_ephemeris(source, request, earth)
    assert len(first_result.times_utc) == 3
    assert first_result.itrs_position_km is not None
    assert first_result.gcrs_position_km is not None
    first_csv, first_metadata = export_ephemeris(first_result, tmp_path / "before.csv")
    original_csv = first_csv.read_bytes()
    original_metadata = first_metadata.read_bytes()

    clock[0] += timedelta(hours=2)
    newer = service.resolve_satellite(source)
    assert len(gp_requests) == 2
    assert newer.sha256 != source.sha256
    assert newer.payload["EPOCH"] != source.payload["EPOCH"]
    assert first_result.satellite.sha256 == source.sha256
    assert first_result.satellite.payload["EPOCH"] == source.payload["EPOCH"]

    newer_result = compute_ephemeris(newer, request, earth)
    assert newer_result.satellite.sha256 == newer.sha256
    assert newer_result.teme_position_km[0, 0] != first_result.teme_position_km[0, 0]

    again_csv, again_metadata = export_ephemeris(first_result, tmp_path / "again.csv")
    assert again_csv.read_bytes() == original_csv
    assert again_metadata.read_bytes() == original_metadata
    assert first_csv.read_bytes() == original_csv
    assert first_metadata.read_bytes() == original_metadata
