"""Atomic local GP/TLE import and reopen after the source disappears."""

import json

import pytest

from orbit_wizard_blue.data import DataService
from orbit_wizard_blue.local_data import LocalDataService
from orbit_wizard_blue.models import ValidationError


_GP = {
    "OBJECT_NAME": "테스트 위성",
    "NORAD_CAT_ID": 12345,
    "EPOCH": "2026-10-15T00:00:00.000000",
    "MEAN_MOTION": 15.0,
    "ECCENTRICITY": 0.001,
    "INCLINATION": 51.6,
    "RA_OF_ASC_NODE": 32.0,
    "ARG_OF_PERICENTER": 12.0,
    "MEAN_ANOMALY": 8.0,
}
_LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
_LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"


def test_gp_object_import_reopens_without_original_or_network(tmp_path):
    original = tmp_path / "위성 자료.json"
    original.write_text(json.dumps(_GP, ensure_ascii=False), encoding="utf-8")
    service = LocalDataService(tmp_path / "user")
    imported = service.import_file(original)
    assert len(imported) == 1
    snapshot = imported[0]
    assert snapshot.source_kind == "local"
    assert snapshot.source_format == "gp_json"
    assert snapshot.source_metadata["filename"] == original.name
    assert snapshot.source_metadata["record_index"] == 0
    original.unlink()
    reopened = LocalDataService(tmp_path / "user").load_record(snapshot.source_metadata["file_sha256"], 0)
    assert reopened.sha256 == snapshot.sha256
    assert reopened.payload["OBJECT_NAME"] == "테스트 위성"
    assert DataService(tmp_path / "cache", opener=lambda *args, **kwargs: pytest.fail("network used")).resolve_satellite(reopened) is reopened


def test_tle_multirecord_import_preserves_order_and_raw_lines(tmp_path):
    original = tmp_path / "orbit.txt"
    original.write_text(f"0 VANGUARD 1\n{_LINE1}\n{_LINE2}\n{_LINE1}\n{_LINE2}\n", encoding="utf-8")
    service = LocalDataService(tmp_path / "user")
    records = service.import_file(original)
    assert len(records) == 2
    assert [record.source_metadata["record_index"] for record in records] == [0, 1]
    assert records[0].source_metadata["raw_tle"].startswith("0 VANGUARD 1\n")
    assert records[1].payload["OBJECT_NAME"] == "NORAD 5"
    original.unlink()
    reopened = service.load_import(records[0].source_metadata["file_sha256"])
    assert [item.sha256 for item in reopened] == [item.sha256 for item in records]


def test_one_invalid_gp_record_cancels_entire_import(tmp_path):
    original = tmp_path / "bad.json"
    original.write_text(json.dumps([_GP, {**_GP, "ECCENTRICITY": 1.5}]), encoding="utf-8")
    service = LocalDataService(tmp_path / "user")
    with pytest.raises(ValidationError, match="record #2"):
        service.import_file(original)
    assert list(service.import_dir.iterdir()) == []


def test_nonfinite_extra_gp_value_cannot_enter_export_metadata(tmp_path):
    original = tmp_path / "nonfinite.json"
    original.write_text(json.dumps({**_GP, "EXTRA": {"quality": float("nan")}}), encoding="utf-8")
    service = LocalDataService(tmp_path / "user")
    with pytest.raises(ValidationError, match="non-finite"):
        service.import_file(original)
    assert list(service.import_dir.iterdir()) == []


def test_one_invalid_tle_record_cancels_entire_import(tmp_path):
    original = tmp_path / "bad.tle"
    original.write_text(f"{_LINE1}\n{_LINE2}\n{_LINE1}\n{_LINE2[:-1]}0\n", encoding="utf-8")
    service = LocalDataService(tmp_path / "user")
    with pytest.raises(ValidationError, match=r"record #2:.*checksum"):
        service.import_file(original)
    assert list(service.import_dir.iterdir()) == []


def test_file_limit_is_enforced_before_import(tmp_path, monkeypatch):
    import orbit_wizard_blue.local_data as local_data

    monkeypatch.setattr(local_data, "MAX_FILE_BYTES", 100)
    original = tmp_path / "too_big.txt"
    original.write_bytes(b"x" * 101)
    service = LocalDataService(tmp_path / "user")
    with pytest.raises(ValidationError, match="exceeds"):
        service.import_file(original)
    assert list(service.import_dir.iterdir()) == []


def test_corrupt_import_manifest_is_reported_as_validation_error(tmp_path):
    original = tmp_path / "valid.json"
    original.write_text(json.dumps(_GP), encoding="utf-8")
    service = LocalDataService(tmp_path / "user")
    snapshot = service.import_file(original)[0]
    digest = snapshot.source_metadata["file_sha256"]
    (service.import_dir / f"{digest}.meta.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValidationError, match="metadata is invalid"):
        service.load_import(digest)
