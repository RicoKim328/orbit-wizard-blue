"""Per-key cache coordination across independent app processes."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
import multiprocessing
from pathlib import Path
from threading import Event, Lock
import time
from urllib.error import URLError

import pytest

from orbit_wizard_blue.cache_lock import process_lock
from orbit_wizard_blue.models import CancelledError


_GP = {
    "OBJECT_NAME": "TEST SAT",
    "NORAD_CAT_ID": 12345,
    "EPOCH": "2026-10-15T00:00:00.000000",
    "MEAN_MOTION": 15.0,
    "ECCENTRICITY": 0.001,
    "INCLINATION": 51.6,
    "RA_OF_ASC_NODE": 32.0,
    "ARG_OF_PERICENTER": 12.0,
    "MEAN_ANOMALY": 8.0,
}


def _cache_worker(cache_dir, start, counter, result_queue):
    from orbit_wizard_blue.data import DataService

    class Response:
        status = 200
        headers = {}

        def __init__(self):
            self.stream = BytesIO(json.dumps([_GP]).encode())

        def read(self, size=-1):
            return self.stream.read(size)

        def close(self):
            self.stream.close()

    def opener(request, timeout):
        with counter.get_lock():
            counter.value += 1
        time.sleep(0.3)
        return Response()

    if not start.wait(5):
        result_queue.put((False, "start timeout"))
        return
    try:
        snapshot = DataService(Path(cache_dir), opener=opener).get_satellite("12345")
        result_queue.put((True, snapshot.sha256))
    except Exception as exc:
        result_queue.put((False, repr(exc)))


def test_two_processes_share_one_download(tmp_path):
    context = multiprocessing.get_context("spawn")
    start = context.Event()
    counter = context.Value("i", 0)
    results = context.Queue()
    workers = [
        context.Process(target=_cache_worker, args=(str(tmp_path), start, counter, results))
        for _ in range(2)
    ]
    for worker in workers:
        worker.start()
    start.set()
    try:
        for worker in workers:
            worker.join(timeout=12)
        assert all(worker.exitcode == 0 for worker in workers)
        outcomes = [results.get(timeout=2) for _ in workers]
        assert all(ok for ok, _ in outcomes), outcomes
        assert outcomes[0][1] == outcomes[1][1]
        assert counter.value == 1
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=2)


def test_waiting_for_process_lock_can_be_cancelled(tmp_path):
    path = tmp_path / "busy.lock"
    stopped = Event()
    announced = Event()

    def check_cancel():
        if stopped.is_set():
            raise CancelledError()

    def waiter():
        with process_lock(path, check_cancel, announced.set):
            pytest.fail("Lock should remain occupied until cancellation")

    with process_lock(path, lambda: None):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(waiter)
            assert announced.wait(2)
            stopped.set()
            with pytest.raises(CancelledError):
                future.result(timeout=3)


def test_concurrent_initial_force_earth_fetches_each_source_once(tmp_path):
    from astropy.utils import iers
    from orbit_wizard_blue.data import DataService

    counts = {"iers": 0, "leap": 0}
    guard = Lock()
    start = Event()
    iers_bytes = Path(iers.IERS_A_FILE).read_bytes()
    leap_bytes = Path(iers.IERS_LEAP_SECOND_FILE).read_bytes()

    class Response:
        status = 200
        headers = {}

        def __init__(self, payload):
            self.stream = BytesIO(payload)

        def read(self, size=-1):
            return self.stream.read(size)

        def close(self):
            self.stream.close()

    def opener(request, timeout):
        kind = "iers" if "finals2000A" in request.full_url else "leap"
        with guard:
            counts[kind] += 1
        time.sleep(0.15)
        return Response(iers_bytes if kind == "iers" else leap_bytes)

    service = DataService(tmp_path, opener=opener)

    def fetch():
        assert start.wait(2)
        return service.get_earth_data(force=True)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(fetch) for _ in range(2)]
        start.set()
        results = [future.result(timeout=10) for future in futures]
    assert counts == {"iers": 1, "leap": 1}
    assert all(result.provenance["iers"]["kind"] == "downloaded" for result in results)


def test_concurrent_failed_force_returns_same_stale_cache(tmp_path):
    from orbit_wizard_blue.data import DataService

    now = [datetime(2026, 10, 15, tzinfo=timezone.utc)]
    entered = Event()
    release = Event()
    waiting = Event()
    calls = 0

    class Response:
        status = 200
        headers = {}

        def __init__(self):
            self.stream = BytesIO(json.dumps([_GP]).encode())

        def read(self, size=-1):
            return self.stream.read(size)

        def close(self):
            self.stream.close()

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            return Response()
        entered.set()
        assert release.wait(3)
        raise URLError("offline")

    service = DataService(tmp_path, opener=opener, clock=lambda: now[0])
    original = service.get_satellite("12345")
    now[0] += timedelta(hours=2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(service.get_satellite, "12345", force=True)
        assert entered.wait(3)
        second = executor.submit(service.get_satellite, "12345", force=True, status=lambda _: waiting.set())
        try:
            assert waiting.wait(3)
        finally:
            release.set()
        results = [first.result(timeout=3), second.result(timeout=3)]
    assert calls == 2
    assert all(result.stale and result.sha256 == original.sha256 for result in results)
    assert all(result.checked_at == original.checked_at for result in results)
