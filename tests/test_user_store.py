"""Persistent recent actions and favorites across restarts and processes."""

from concurrent.futures import ThreadPoolExecutor
import json
import multiprocessing

from orbit_wizard_blue.local_data import LocalDataService
from orbit_wizard_blue.models import DataSnapshot
from orbit_wizard_blue.user_store import UserStore


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


def _online_snapshot():
    return DataSnapshot(_GP, "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=json",
                        "2026-10-15T00:00:00Z", "2026-10-15T00:00:00Z", "abc")


def test_recent_deduplicates_moves_to_front_and_caps_at_twenty(tmp_path):
    store = UserStore(tmp_path)
    store.record_recent("online_query", "ISS")
    store.record_recent("online_query", "Hubble")
    store.record_recent("online_query", "iss", label="ISS again")
    assert [entry.query for entry in store.list_recent()] == ["iss", "Hubble"]
    assert store.remove_recent(store.list_recent()[1].key)
    assert not store.remove_recent("online:absent")
    assert [entry.query for entry in store.list_recent()] == ["iss"]
    for index in range(25):
        store.record_recent("online_query", f"sat-{index}")
    restarted = UserStore(tmp_path)
    recent = restarted.list_recent()
    assert len(recent) == 20
    assert recent[0].query == "sat-24"
    assert recent[-1].query == "sat-5"
    assert all(entry.kind == "online_query" and entry.at_utc.endswith("Z") for entry in recent)
    restarted.clear_recent()
    assert store.list_recent() == []


def test_local_recent_and_favorite_reopen_without_original(tmp_path):
    original = tmp_path / "위성.json"
    original.write_text(json.dumps([_GP], ensure_ascii=False), encoding="utf-8")
    local = LocalDataService(tmp_path / "user")
    snapshot = local.import_file(original)[0]
    digest = snapshot.source_metadata["file_sha256"]
    store = UserStore(tmp_path / "user")
    store.record_recent("local_import", original.name, file_sha256=digest)
    key = store.add_favorite(snapshot)
    assert key == f"local:{digest}:0"
    original.unlink()

    reopened_store = UserStore(tmp_path / "user")
    recent = reopened_store.list_recent()[0]
    assert recent.kind == "local_import"
    assert recent.file_sha256 == digest
    assert recent.record_index is None
    assert local.load_import(recent.file_sha256)[0].sha256 == snapshot.sha256
    favorite = reopened_store.list_favorites()[0]
    assert favorite.snapshot.sha256 == snapshot.sha256
    assert favorite.file_sha256 == digest and favorite.record_index == 0
    assert local.load_record(favorite.file_sha256, favorite.record_index).sha256 == snapshot.sha256
    assert reopened_store.remove_favorite(key)
    assert not reopened_store.remove_favorite(key)


def test_online_favorite_keeps_snapshot_for_offline_display(tmp_path):
    store = UserStore(tmp_path)
    snapshot = _online_snapshot()
    assert store.add_favorite(snapshot) == "online:25544"
    reopened = UserStore(tmp_path)
    favorite = reopened.list_favorites()[0]
    assert favorite.label == "ISS (ZARYA)"
    assert favorite.snapshot.payload["NORAD_CAT_ID"] == 25544
    assert favorite.file_sha256 is None
    reopened.clear_favorites()
    assert store.list_favorites() == []


def test_concurrent_recent_writes_use_separate_transactions(tmp_path):
    store = UserStore(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda number: store.record_recent("online_query", f"query-{number}"), range(40)))
    assert len(UserStore(tmp_path).list_recent()) == 20


def _store_writer(data_dir, prefix, start):
    store = UserStore(data_dir)
    if not start.wait(5):
        raise RuntimeError("start timeout")
    for index in range(15):
        store.record_recent("online_query", f"{prefix}-{index}")


def test_two_processes_write_recent_actions_safely(tmp_path):
    context = multiprocessing.get_context("spawn")
    start = context.Event()
    workers = [context.Process(target=_store_writer, args=(tmp_path, prefix, start)) for prefix in ("A", "B")]
    for worker in workers:
        worker.start()
    start.set()
    try:
        for worker in workers:
            worker.join(timeout=12)
        assert all(worker.exitcode == 0 for worker in workers)
        recent = UserStore(tmp_path).list_recent()
        assert len(recent) == 20
        assert len({entry.query for entry in recent}) == 20
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=2)
