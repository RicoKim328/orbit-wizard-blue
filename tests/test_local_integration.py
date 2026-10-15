"""Exercise offline local imports through compute, audit export, and reopen."""

import csv
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from urllib.error import URLError

import numpy as np
import pytest

from orbit_wizard_blue.data import DataService, GP_URL
from orbit_wizard_blue.export import export_ephemeris
from orbit_wizard_blue.local_data import LocalDataService
from orbit_wizard_blue.models import OrbitRequest
from orbit_wizard_blue.orbit import compute_ephemeris
from orbit_wizard_blue.user_store import UserStore


_GP = {
    "OBJECT_NAME": "VANGUARD 1",
    "NORAD_CAT_ID": 5,
    "EPOCH": "2000-06-27T18:50:19.733568",
    "MEAN_MOTION": 10.82419157,
    "ECCENTRICITY": 0.1859667,
    "INCLINATION": 34.2682,
    "RA_OF_ASC_NODE": 348.7242,
    "ARG_OF_PERICENTER": 331.7664,
    "MEAN_ANOMALY": 19.3264,
}
_LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
_LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"


@pytest.mark.parametrize("source_format", ["gp_json", "tle"])
def test_local_import_compute_export_favorite_reopen_without_network(tmp_path, source_format):
    original = tmp_path / ("위성.json" if source_format == "gp_json" else "위성.tle")
    if source_format == "gp_json":
        original.write_text(json.dumps(_GP, ensure_ascii=False), encoding="utf-8")
    else:
        original.write_text(f"0 VANGUARD 1\n{_LINE1}\n{_LINE2}\n", encoding="utf-8")
    data_dir = tmp_path / "user"
    local = LocalDataService(data_dir)
    user = UserStore(data_dir)
    source = local.import_file(original)[0]
    local_key = user.add_favorite(source)
    user.record_recent("local_import", original.name, file_sha256=source.source_metadata["file_sha256"])

    requests = []

    def offline(request, timeout):
        requests.append(request.full_url)
        if "gp.php" in request.full_url:
            pytest.fail("Local record triggered a CelesTrak request")
        raise URLError("offline integration test")

    service = DataService(tmp_path / "cache", opener=offline)
    earth = service.get_earth_data()
    selected = service.resolve_satellite(source)
    epoch = datetime.fromisoformat(selected.payload["EPOCH"].replace("Z", "+00:00"))
    if epoch.tzinfo is None:
        epoch = epoch.replace(tzinfo=timezone.utc)
    request = OrbitRequest(epoch, epoch + timedelta(minutes=2), 60)
    first = compute_ephemeris(selected, request, earth)
    assert first.itrs_position_km is not None
    assert first.gcrs_position_km is not None
    first_csv, first_json = export_ephemeris(first, tmp_path / "first.csv")
    metadata = json.loads(first_json.read_text(encoding="utf-8"))
    assert metadata["schema_version"] == 2
    assert metadata["source"]["kind"] == "local"
    assert metadata["source"]["format"] == source_format
    assert metadata["source"]["metadata"]["file_sha256"] == source.source_metadata["file_sha256"]
    assert metadata["sample_count"] == 3
    if source_format == "tle":
        assert metadata["source"]["metadata"]["raw_tle"] == f"0 VANGUARD 1\n{_LINE1}\n{_LINE2}"
    with first_csv.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3
    assert all(row["norad_id"] == "5" for row in rows)
    original_csv_bytes, original_json_bytes = first_csv.read_bytes(), first_json.read_bytes()

    original.unlink()
    reopened_user = UserStore(data_dir)
    favorites = reopened_user.list_favorites()
    assert len(favorites) == 1 and favorites[0].key == local_key
    reopened_local = LocalDataService(data_dir)
    reopened = reopened_local.load_record(favorites[0].file_sha256, favorites[0].record_index)
    assert reopened.sha256 == favorites[0].snapshot.sha256 == source.sha256
    again = compute_ephemeris(service.resolve_satellite(reopened), request, earth)
    np.testing.assert_array_equal(first.teme_position_km, again.teme_position_km)
    np.testing.assert_array_equal(first.itrs_position_km, again.itrs_position_km)
    again_csv, again_json = export_ephemeris(again, tmp_path / "again.csv")
    assert again_csv.read_bytes() == original_csv_bytes
    assert again_json.read_bytes() == original_json_bytes
    assert len(requests) == 2  # IERS and leap seconds only, each attempted once.

    online = replace(source, source_kind="online", source_format="gp_json",
                     source_url=f"{GP_URL}?CATNR=5&FORMAT=json", source_metadata={})
    online_key = reopened_user.add_favorite(online)
    assert online_key == "online:5"
    assert {item.key for item in reopened_user.list_favorites()} == {local_key, online_key}
