"""On-demand CelesTrak and Earth-reference downloads with a persistent cache."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

from platformdirs import user_cache_dir

from .models import CancelledError, DataSnapshot, EarthData, ValidationError, thaw_json
from .cache_lock import process_lock, thread_lock
from .validation import gp_items


CACHE_SECONDS = 7200
TIMEOUT_SECONDS = 8
GP_URL = "https://celestrak.org/NORAD/elements/gp.php"
_LOCKS_GUARD = threading.Lock()
_LOCKS: dict[str, threading.Lock] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except ValueError:
        return None


def _check_cancel(cancel: Any) -> None:
    if cancel is None:
        return
    if callable(cancel):
        stopped = cancel()
    elif hasattr(cancel, "is_set"):
        stopped = cancel.is_set()
    else:
        stopped = bool(cancel)
    if stopped:
        raise CancelledError("Data request cancelled")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _lock_for(key: str) -> threading.Lock:
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.Lock())


def _version_path(base: Path, meta: dict[str, Any]) -> Path:
    digest = meta.get("sha256", "")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid cache digest")
    return base.with_name(f"{base.stem}.{digest}{base.suffix}")


def _read_failure(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _headers(response: Any) -> Any:
    return response.headers


def _header(headers: Any, key: str) -> str | None:
    return headers.get(key) if headers is not None else None


def _retry_at(header: str | None, now: datetime) -> datetime | None:
    if not header:
        return None
    try:
        return now + timedelta(seconds=max(0, int(header)))
    except ValueError:
        try:
            value = parsedate_to_datetime(header)
            return value.astimezone(timezone.utc) if value.tzinfo else None
        except (TypeError, ValueError):
            return None


def _gp_items(raw: bytes) -> list[dict[str, Any]]:
    return gp_items(raw)


def _search_items(raw: bytes) -> list[dict[str, Any]]:
    return gp_items(raw, allow_empty=True)


def _read_limited(response: Any, limit: int, cancel: Any) -> bytes:
    content = bytearray()
    while len(content) <= limit:
        _check_cancel(cancel)
        chunk = response.read(min(65_536, limit + 1 - len(content)))
        _check_cancel(cancel)
        if not chunk:
            break
        content.extend(chunk)
    return bytes(content)


class DataService:
    """Resolve all external inputs through one two-hour, persistent disk cache.

    ``opener`` and ``clock`` are injectable for deterministic, offline tests.
    The opener follows ``urllib.request.urlopen``'s response protocol.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        *,
        opener: Callable[..., Any] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir is not None else Path(user_cache_dir("orbit-wizard-blue"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._opener = opener or urlopen
        self._clock = clock or _utcnow
        # Explicitly selected reference data below replace Astropy's implicit network path.
        from astropy.utils import iers

        iers.conf.auto_download = False
        # Astropy's leap-second auto_open checks its own remote URL cache even
        # with auto_download=False. Keep that lookup inside our data manager.
        iers.conf.iers_leap_second_auto_url = ""
        iers.conf.ietf_leap_second_auto_url = ""

    def search_satellites(
        self, query: str, force: bool = False, cancel: Any = None,
        status: Callable[[str], None] | None = None,
    ) -> list[DataSnapshot]:
        query = query.strip()
        if not query:
            raise ValidationError("Enter a satellite name or NORAD ID")
        if query.isdigit():
            return [self.get_satellite(query, force=force, cancel=cancel, status=status)]
        if len(query) > 200 or any(ord(character) < 32 for character in query):
            raise ValidationError("Invalid satellite name")
        url = f"{GP_URL}?{urlencode({'NAME': query, 'FORMAT': 'json'})}"
        raw, meta, stale, warning, _ = self._fetch(url, "gp_search", force, _search_items, cancel, status)
        return [self._snapshot(item, meta, stale, warning) for item in _search_items(raw)]

    def get_satellite(
        self, norad_id: str, force: bool = False, cancel: Any = None,
        status: Callable[[str], None] | None = None,
    ) -> DataSnapshot:
        norad_id = str(norad_id).strip()
        if not re.fullmatch(r"[0-9]+", norad_id):
            raise ValidationError("NORAD ID must contain only digits")
        url = f"{GP_URL}?{urlencode({'CATNR': norad_id, 'FORMAT': 'json'})}"
        def validate_number(raw: bytes) -> None:
            items = _gp_items(raw)
            if len(items) != 1 or str(items[0]["NORAD_CAT_ID"]) != str(int(norad_id)):
                raise ValidationError("CelesTrak returned a different NORAD ID")

        raw, meta, stale, warning, _ = self._fetch(url, "gp", force, validate_number, cancel, status)
        items = _gp_items(raw)
        matching = [item for item in items if str(item["NORAD_CAT_ID"]) == str(int(norad_id))]
        if len(matching) != 1:
            raise ValidationError("CelesTrak returned a different NORAD ID")
        return self._snapshot(matching[0], meta, stale, warning)

    def resolve_satellite(
        self, snapshot: DataSnapshot, force: bool = False, cancel: Any = None,
        status: Callable[[str], None] | None = None,
    ) -> DataSnapshot:
        """Recheck a selected record's original query before a calculation.

        Reusing its NAME query avoids a redundant CATNR download after search.
        The returned snapshot is independent of any earlier result.
        """
        _check_cancel(cancel)
        if snapshot.source_kind == "local":
            if snapshot.source_format not in ("gp_json", "tle"):
                raise ValidationError("Unsupported local satellite format")
            gp_items(json.dumps([thaw_json(snapshot.payload)]).encode())
            return snapshot
        if snapshot.source_kind != "online":
            raise ValidationError("Unsupported satellite source kind")
        source = urlsplit(snapshot.source_url)
        expected = urlsplit(GP_URL)
        if (source.scheme, source.netloc, source.path, source.fragment) != (
            expected.scheme, expected.netloc, expected.path, ""
        ):
            raise ValidationError("Snapshot has an unsupported GP source")
        params = parse_qs(source.query, strict_parsing=True)
        if params.get("FORMAT") != ["json"]:
            raise ValidationError("Snapshot has an unsupported GP format")
        if set(params) == {"CATNR", "FORMAT"} and len(params["CATNR"]) == 1:
            kind = "gp"
            if not params["CATNR"][0].isdigit():
                raise ValidationError("Snapshot has an invalid NORAD query")
        elif set(params) == {"NAME", "FORMAT"} and len(params["NAME"]) == 1:
            kind = "gp_search"
        else:
            raise ValidationError("Snapshot has an unsupported GP query")
        try:
            norad_id = str(int(snapshot.payload["NORAD_CAT_ID"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError("Snapshot has an invalid NORAD ID") from exc
        if kind == "gp" and str(int(params["CATNR"][0])) != norad_id:
            raise ValidationError("Snapshot source and NORAD ID disagree")
        if kind == "gp":
            def validator(raw: bytes) -> list[dict[str, Any]]:
                items = _gp_items(raw)
                if len(items) != 1 or str(items[0]["NORAD_CAT_ID"]) != norad_id:
                    raise ValidationError("CelesTrak returned a different NORAD ID")
                return items
        else:
            validator = _search_items
        raw, meta, stale, warning, _ = self._fetch(snapshot.source_url, kind, force, validator, cancel, status)
        matches = [item for item in validator(raw) if str(item["NORAD_CAT_ID"]) == norad_id]
        if len(matches) != 1:
            raise ValidationError("Selected satellite is unavailable in its source query")
        return self._snapshot(matches[0], meta, stale, warning)

    @staticmethod
    def _snapshot(item: dict[str, Any], meta: dict[str, Any], stale: bool, warning: str) -> DataSnapshot:
        return DataSnapshot(
            payload=item,
            source_url=meta["source_url"],
            fetched_at=meta["fetched_at"],
            checked_at=meta["checked_at"],
            sha256=meta["sha256"],
            stale=stale,
            warning=warning,
        )

    def get_earth_data(
        self, force: bool = False, cancel: Any = None,
        status: Callable[[str], None] | None = None,
    ) -> EarthData:
        from astropy.utils import iers

        iers.conf.auto_download = False
        resources = (
            ("iers", iers.IERS_A_URL, Path(iers.IERS_A_FILE), lambda path: iers.IERS_A.open(str(path), cache=False)),
            ("leap_seconds", iers.IERS_LEAP_SECOND_URL, Path(iers.IERS_LEAP_SECOND_FILE), lambda path: iers.LeapSeconds.open(str(path), cache=False)),
        )
        paths: dict[str, Path] = {}
        provenance: dict[str, Any] = {}
        warnings: list[str] = []
        for name, url, bundled_path, validator in resources:
            _check_cancel(cancel)
            try:
                _, meta, stale, warning, path = self._fetch(
                    url, name, force, lambda raw, check_path: validator(check_path), cancel, status
                )
                paths[name] = path
                provenance[name] = {**meta, "kind": "downloaded", "stale": stale}
                if warning:
                    warnings.append(f"{name}: {warning}")
            except (OSError, URLError, HTTPError, ValidationError, RuntimeError) as exc:
                validator(bundled_path)
                paths[name] = bundled_path
                provenance[name] = {
                    "kind": "bundled",
                    "source_url": str(bundled_path),
                    "sha256": sha256(bundled_path.read_bytes()).hexdigest(),
                    "fetched_at": "",
                    "checked_at": "",
                    "stale": True,
                }
                warnings.append(f"{name}: using bundled data ({exc})")
        return EarthData(paths["iers"], paths["leap_seconds"], provenance, "; ".join(warnings))

    def _paths(self, url: str, kind: str) -> tuple[Path, Path, Path, Path]:
        stem = sha256(f"{kind}:{url}".encode()).hexdigest()
        extension = ".json" if kind.startswith("gp") else ".dat"
        return (
            self.cache_dir / f"{stem}{extension}",
            self.cache_dir / f"{stem}.meta.json",
            self.cache_dir / f"{stem}.throttle.json",
            self.cache_dir / f"{stem}.failure.json",
        )

    def _read_cache(self, content_path: Path, meta_path: Path, url: str) -> tuple[bytes, dict[str, Any]] | None:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            raw = _version_path(content_path, meta).read_bytes()
            if meta["source_url"] != url or meta["sha256"] != sha256(raw).hexdigest():
                return None
            if _parse_time(meta["fetched_at"]) is None or _parse_time(meta["checked_at"]) is None:
                return None
            return raw, meta
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _fetch(
        self,
        url: str,
        kind: str,
        force: bool,
        validator: Callable[..., Any],
        cancel: Any,
        status: Callable[[str], None] | None = None,
    ) -> tuple[bytes, dict[str, Any], bool, str, Path]:
        content_path, meta_path, throttle_path, failure_path = self._paths(url, kind)
        key = str(content_path)
        before = self._read_cache(content_path, meta_path, url)
        before_failure = _read_failure(failure_path)
        def check_cancel() -> None:
            _check_cancel(cancel)

        def on_wait() -> None:
            if status is not None:
                label = {
                    "gp": "위성 자료", "gp_search": "위성 검색",
                    "iers": "지구 회전 자료", "leap_seconds": "윤초 자료",
                }.get(kind, "외부 자료")
                status(f"{label} 캐시 잠금을 기다리는 중…")

        with thread_lock(_lock_for(key), check_cancel, on_wait), process_lock(
            content_path.with_suffix(".lock"), check_cancel, on_wait
        ):
            _check_cancel(cancel)
            cached = self._read_cache(content_path, meta_path, url)
            now = self._clock()
            if cached is not None:
                raw, meta = cached
                checked = _parse_time(meta["checked_at"])
                if before is None or before[1].get("check_id") != meta.get("check_id"):
                    return raw, meta, False, "", _version_path(content_path, meta)
                # CelesTrak permits one GP download per two-hour update.
                # A manual refresh cannot bypass the provider's own schedule.
                if kind.startswith("gp") and checked is not None and now - checked < timedelta(seconds=CACHE_SECONDS):
                    warning = (
                        f"CelesTrak permits the next GP check after {_iso(checked + timedelta(seconds=CACHE_SECONDS))}"
                        if force else ""
                    )
                    return raw, meta, False, warning, _version_path(content_path, meta)
                if not force and checked is not None and now - checked < timedelta(seconds=CACHE_SECONDS):
                    return raw, meta, False, "", _version_path(content_path, meta)
            else:
                raw, meta = b"", {}
            try:
                throttle = json.loads(throttle_path.read_text(encoding="utf-8"))
                retry = _parse_time(throttle.get("retry_at"))
            except (OSError, ValueError, TypeError):
                retry = None
            if retry is not None and now < retry:
                message = f"Provider retry allowed after {_iso(retry)}"
                if cached is not None:
                    return raw, meta, True, message, _version_path(content_path, meta)
                raise RuntimeError(message)
            failure = _read_failure(failure_path)
            if failure and failure.get("failure_id") != before_failure.get("failure_id"):
                message = f"Concurrent refresh failed: {failure.get('error', 'source unavailable')}"
                if cached is not None:
                    return raw, meta, True, message, _version_path(content_path, meta)
                raise RuntimeError(message)
            if not force:
                attempted = _parse_time(failure.get("last_attempt_at"))
                if attempted is not None and now < attempted + timedelta(seconds=CACHE_SECONDS):
                    message = (
                        f"Last refresh failed; retry after {_iso(attempted + timedelta(seconds=CACHE_SECONDS))}: "
                        f"{failure.get('error', 'source unavailable')}"
                    )
                    if cached is not None:
                        return raw, meta, True, message, _version_path(content_path, meta)
                    raise RuntimeError(message)
            headers = {"User-Agent": "orbit-wizard-blue/1.0"}
            if cached is not None:
                if meta.get("etag"):
                    headers["If-None-Match"] = meta["etag"]
                if meta.get("last_modified"):
                    headers["If-Modified-Since"] = meta["last_modified"]
            try:
                request = Request(url, headers=headers)
                response = self._opener(request, timeout=TIMEOUT_SECONDS)
                try:
                    status = getattr(response, "status", None) or response.getcode()
                    if status == 304:
                        if cached is None:
                            raise ValidationError("Unexpected 304 without cached data")
                        new_meta = {**meta, "checked_at": _iso(now), "check_id": uuid4().hex}
                        _atomic_write(meta_path, json.dumps(new_meta).encode())
                        failure_path.unlink(missing_ok=True)
                        return raw, new_meta, False, "", _version_path(content_path, new_meta)
                    if status != 200:
                        raise RuntimeError(f"HTTP {status}")
                    limit = 5_000_000 if kind.startswith("gp") else 20_000_000
                    fresh = _read_limited(response, limit, cancel)
                    if not fresh or len(fresh) > limit:
                        raise ValidationError("Provider response is empty or too large")
                    _check_cancel(cancel)
                    if kind.startswith("gp"):
                        validator(fresh)
                    else:
                        with tempfile.TemporaryDirectory(dir=self.cache_dir) as temp_dir:
                            temp_path = Path(temp_dir) / "candidate.dat"
                            temp_path.write_bytes(fresh)
                            validator(fresh, temp_path)
                    _check_cancel(cancel)
                    fresh_meta = {
                        "source_url": url,
                        "fetched_at": _iso(now),
                        "checked_at": _iso(now),
                        "sha256": sha256(fresh).hexdigest(),
                        "etag": _header(_headers(response), "ETag"),
                        "last_modified": _header(_headers(response), "Last-Modified"),
                        "check_id": uuid4().hex,
                    }
                    _atomic_write(_version_path(content_path, fresh_meta), fresh)
                    _atomic_write(meta_path, json.dumps(fresh_meta).encode())
                    failure_path.unlink(missing_ok=True)
                    return fresh, fresh_meta, False, "", _version_path(content_path, fresh_meta)
                finally:
                    response.close()
            except HTTPError as exc:
                try:
                    if exc.code == 304 and cached is not None:
                        new_meta = {**meta, "checked_at": _iso(now), "check_id": uuid4().hex}
                        _atomic_write(meta_path, json.dumps(new_meta).encode())
                        failure_path.unlink(missing_ok=True)
                        return raw, new_meta, False, "", _version_path(content_path, new_meta)
                    if exc.code == 404 and kind == "gp_search":
                        empty = _read_limited(exc, 5_000_000, cancel)
                        if len(empty) <= 5_000_000 and empty.strip() == b"No GP data found":
                            empty_meta = {
                                "source_url": url,
                                "fetched_at": _iso(now),
                                "checked_at": _iso(now),
                                "sha256": sha256(empty).hexdigest(),
                                "etag": None,
                                "last_modified": None,
                                "check_id": uuid4().hex,
                            }
                            _atomic_write(_version_path(content_path, empty_meta), empty)
                            _atomic_write(meta_path, json.dumps(empty_meta).encode())
                            failure_path.unlink(missing_ok=True)
                            return empty, empty_meta, False, "", _version_path(content_path, empty_meta)
                    if exc.code in (403, 429, 503):
                        retry = _retry_at(_header(exc.headers, "Retry-After"), now)
                        if retry is None and exc.code == 403 and kind.startswith("gp"):
                            retry = now + timedelta(seconds=CACHE_SECONDS)
                        if retry is not None:
                            _atomic_write(throttle_path, json.dumps({"retry_at": _iso(retry)}).encode())
                    error: Exception = exc
                finally:
                    exc.close()
            except (OSError, URLError, ValueError, RuntimeError) as exc:
                error = exc
            _check_cancel(cancel)
            _atomic_write(failure_path, json.dumps({
                "last_attempt_at": _iso(now), "failure_id": uuid4().hex, "error": str(error)
            }).encode())
            if cached is not None:
                return raw, meta, True, f"Refresh failed: {error}", _version_path(content_path, meta)
            raise RuntimeError(f"Data unavailable from {url}: {error}") from error
