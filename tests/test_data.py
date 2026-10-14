"""Offline checks for the shared persistent external-data cache."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
from pathlib import Path
from threading import Event
from urllib.error import HTTPError, URLError

import pytest

from orbit_wizard_blue.data import CACHE_SECONDS, DataService
from orbit_wizard_blue.models import CancelledError


GP = {
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


class Response:
    def __init__(self, body, status=200, headers=None):
        self.stream = BytesIO(body)
        self.status = status
        self.headers = headers or {}

    def read(self):
        return self.stream.read()

    def getcode(self):
        return self.status

    def close(self):
        self.stream.close()


def body(name="TEST SAT"):
    return json.dumps([{**GP, "OBJECT_NAME": name}]).encode()


def test_ttl_persists_across_restart_and_boundary(tmp_path):
    now = [datetime(2026, 10, 15, tzinfo=timezone.utc)]
    requests = []

    def opener(request, timeout):
        requests.append(request)
        return Response(body(), headers={"ETag": '"v1"'})

    first = DataService(tmp_path, opener=opener, clock=lambda: now[0])
    original = first.get_satellite("12345")
    now[0] += timedelta(seconds=CACHE_SECONDS - 1)
    restarted = DataService(tmp_path, opener=opener, clock=lambda: now[0])
    assert restarted.get_satellite("12345").sha256 == original.sha256
    assert len(requests) == 1
    now[0] += timedelta(seconds=1)
    restarted.get_satellite("12345")
    assert len(requests) == 2
    assert requests[-1].get_header("If-none-match") == '"v1"'


def test_manual_force_and_not_modified_preserve_fetch_time(tmp_path):
    now = [datetime(2026, 10, 15, tzinfo=timezone.utc)]
    requests = []

    def opener(request, timeout):
        requests.append(request)
        if len(requests) == 1:
            return Response(body(), headers={"ETag": '"v1"'})
        raise HTTPError(request.full_url, 304, "Not Modified", {}, None)

    service = DataService(tmp_path, opener=opener, clock=lambda: now[0])
    old = service.get_satellite("12345")
    now[0] += timedelta(hours=2)
    new = service.get_satellite("12345", force=True)
    assert len(requests) == 2
    assert new.fetched_at == old.fetched_at
    assert new.checked_at != old.checked_at
    assert not new.stale


def test_manual_force_respects_celestrak_two_hour_policy(tmp_path):
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        return Response(body())

    service = DataService(tmp_path, opener=opener)
    first = service.get_satellite("12345")
    again = service.get_satellite("12345", force=True)
    assert calls == 1
    assert again.checked_at == first.checked_at
    assert "next GP check" in again.warning


def test_invalid_refresh_retains_last_good_and_does_not_freshen(tmp_path):
    now = [datetime(2026, 10, 15, tzinfo=timezone.utc)]
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        return Response(body() if calls == 1 else b"<html>bad</html>")

    service = DataService(tmp_path, opener=opener, clock=lambda: now[0])
    old = service.get_satellite("12345")
    now[0] += timedelta(hours=2)
    stale = service.get_satellite("12345")
    assert stale.stale and stale.warning
    assert stale.sha256 == old.sha256
    assert stale.checked_at == old.checked_at
    service.get_satellite("12345")
    assert calls == 3


def test_retry_after_blocks_manual_force_and_survives_restart(tmp_path):
    now = [datetime(2026, 10, 15, tzinfo=timezone.utc)]
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            return Response(body())
        if calls == 2:
            raise HTTPError(request.full_url, 429, "rate limited", {"Retry-After": "120"}, None)
        return Response(body("NEW"))

    service = DataService(tmp_path, opener=opener, clock=lambda: now[0])
    service.get_satellite("12345")
    now[0] += timedelta(hours=2)
    assert service.get_satellite("12345", force=True).stale
    restarted = DataService(tmp_path, opener=opener, clock=lambda: now[0])
    assert restarted.get_satellite("12345", force=True).stale
    assert calls == 2
    now[0] += timedelta(seconds=120)
    assert restarted.get_satellite("12345", force=True).payload["OBJECT_NAME"] == "NEW"


def test_celestrak_block_backs_off_for_two_hours(tmp_path):
    now = [datetime(2026, 10, 15, tzinfo=timezone.utc)]
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            return Response(body())
        raise HTTPError(request.full_url, 403, "blocked", {}, None)

    service = DataService(tmp_path, opener=opener, clock=lambda: now[0])
    service.get_satellite("12345")
    now[0] += timedelta(hours=2)
    assert service.get_satellite("12345").stale
    assert "retry allowed after" in service.get_satellite("12345", force=True).warning
    assert calls == 2


def test_concurrent_same_query_downloads_once(tmp_path):
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        return Response(body())

    service = DataService(tmp_path, opener=opener)
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(service.get_satellite, ["12345"] * 8))
    assert calls == 1
    assert len({result.sha256 for result in results}) == 1


def test_search_no_results_is_distinct_from_provider_error(tmp_path):
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if "NAME=missing" in request.full_url:
            raise HTTPError(request.full_url, 404, "Not found", {}, BytesIO(b"No GP data found"))
        raise HTTPError(request.full_url, 503, "Unavailable", {}, None)

    service = DataService(tmp_path, opener=opener)
    assert service.search_satellites("missing") == []
    assert service.search_satellites("missing") == []
    assert calls == 1
    with pytest.raises(RuntimeError, match="Data unavailable"):
        service.search_satellites("other")


def test_resolve_search_selection_reuses_query_and_checks_ttl(tmp_path):
    now = [datetime(2026, 10, 15, tzinfo=timezone.utc)]
    requests = []

    def opener(request, timeout):
        requests.append(request.full_url)
        return Response(body("NEW" if len(requests) == 2 else "OLD"))

    service = DataService(tmp_path, opener=opener, clock=lambda: now[0])
    selected = service.search_satellites("TEST SAT")[0]
    assert service.resolve_satellite(selected).payload["OBJECT_NAME"] == "OLD"
    forced = service.resolve_satellite(selected, force=True)
    assert "next GP check" in forced.warning
    assert len(requests) == 1
    now[0] += timedelta(hours=2)
    refreshed = service.resolve_satellite(selected)
    assert refreshed.payload["OBJECT_NAME"] == "NEW"
    assert len(requests) == 2
    assert all("NAME=TEST+SAT" in url for url in requests)


def test_resolve_rejects_untrusted_snapshot_url(tmp_path):
    from dataclasses import replace

    service = DataService(tmp_path, opener=lambda request, timeout: Response(body()))
    selected = service.search_satellites("TEST SAT")[0]
    with pytest.raises(ValueError, match="unsupported GP source"):
        service.resolve_satellite(replace(selected, source_url="https://example.com/?NAME=TEST"))


def test_cancellation_propagates_without_fallback(tmp_path):
    stopped = Event()
    stopped.set()
    service = DataService(tmp_path, opener=lambda request, timeout: Response(body()))
    with pytest.raises(CancelledError):
        service.get_satellite("12345", cancel=stopped)


def test_earth_data_uses_bundled_files_offline_without_implicit_download(tmp_path):
    from astropy.utils import iers

    def offline(request, timeout):
        raise URLError("offline")

    service = DataService(tmp_path, opener=offline)
    earth = service.get_earth_data()
    assert iers.conf.auto_download is False
    assert earth.iers_path.is_file() and earth.leap_seconds_path.is_file()
    assert earth.provenance["iers"]["kind"] == "bundled"
    assert earth.provenance["leap_seconds"]["kind"] == "bundled"
    assert len(iers.IERS_A.open(str(earth.iers_path))) > 0
    assert len(iers.LeapSeconds.open(str(earth.leap_seconds_path))) > 0


def test_earth_refresh_keeps_prior_result_files_unchanged(tmp_path):
    from astropy.utils import iers

    calls = 0
    original_iers = Path(iers.IERS_A_FILE).read_bytes()
    original_leaps = Path(iers.IERS_LEAP_SECOND_FILE).read_bytes()

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if "finals2000A" in request.full_url:
            return Response(original_iers if calls == 1 else original_iers + b"\n")
        return Response(original_leaps)

    service = DataService(tmp_path, opener=opener)
    first = service.get_earth_data()
    first_bytes = first.iers_path.read_bytes()
    second = service.get_earth_data(force=True)
    assert calls == 4
    assert first.iers_path != second.iers_path
    assert first.iers_path.read_bytes() == first_bytes
    assert second.iers_path.read_bytes() == original_iers + b"\n"
    assert second.provenance["iers"]["kind"] == "downloaded"
