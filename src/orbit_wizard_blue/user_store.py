"""Persistent recent actions and satellite favorites in user data storage."""

from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterator

from platformdirs import user_data_dir

from .models import DataSnapshot, ValidationError, thaw_json


_HASH_PATTERN = re.compile(r"[0-9a-f]{64}")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RecentEntry:
    key: str
    kind: str
    query: str
    label: str
    at_utc: str
    file_sha256: str | None = None
    record_index: int | None = None


@dataclass(frozen=True)
class FavoriteEntry:
    key: str
    label: str
    snapshot: DataSnapshot
    at_utc: str
    file_sha256: str | None = None
    record_index: int | None = None


def _snapshot_json(snapshot: DataSnapshot) -> str:
    value = {
        "payload": thaw_json(snapshot.payload),
        "source_url": snapshot.source_url,
        "fetched_at": snapshot.fetched_at,
        "checked_at": snapshot.checked_at,
        "sha256": snapshot.sha256,
        "stale": snapshot.stale,
        "warning": snapshot.warning,
        "source_kind": snapshot.source_kind,
        "source_format": snapshot.source_format,
        "source_metadata": thaw_json(snapshot.source_metadata),
    }
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def _source_reference(snapshot: DataSnapshot) -> tuple[str | None, int | None]:
    if snapshot.source_kind != "local":
        return None, None
    digest = snapshot.source_metadata.get("file_sha256")
    index = snapshot.source_metadata.get("record_index")
    if not isinstance(digest, str) or not _HASH_PATTERN.fullmatch(digest):
        raise ValidationError("Local snapshot lacks a valid file hash")
    if type(index) is not int or index < 0:
        raise ValidationError("Local snapshot lacks a valid record index")
    return digest, index


class UserStore:
    """SQLite-backed user state; each method owns one short transaction."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else Path(user_data_dir("orbit-wizard-blue"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "user_store.sqlite"
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS recent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dedup_key TEXT NOT NULL UNIQUE,
                    kind TEXT NOT NULL,
                    query TEXT NOT NULL,
                    label TEXT NOT NULL,
                    at_utc TEXT NOT NULL,
                    file_sha256 TEXT,
                    record_index INTEGER
                );
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    label TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    at_utc TEXT NOT NULL,
                    file_sha256 TEXT,
                    record_index INTEGER
                );
            """)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.path, timeout=10)) as connection:
            connection.row_factory = sqlite3.Row
            yield connection

    def record_recent(
        self, kind: str, query: str, label: str = "", snapshot: DataSnapshot | None = None,
        *, file_sha256: str | None = None, record_index: int | None = None,
    ) -> None:
        if kind not in ("online_query", "local_import"):
            raise ValidationError("Unsupported recent-action kind")
        if not isinstance(query, str) or not query.strip():
            raise ValidationError("Recent query must be nonempty text")
        query = query.strip()
        label = label.strip() if isinstance(label, str) else ""
        if snapshot is not None and snapshot.source_kind == "local":
            file_sha256, record_index = _source_reference(snapshot)
        if kind == "local_import":
            if not isinstance(file_sha256, str) or not _HASH_PATTERN.fullmatch(file_sha256):
                raise ValidationError("Recent local import needs a stored file hash")
            if record_index is not None and (type(record_index) is not int or record_index < 0):
                raise ValidationError("Invalid local record index")
            dedup_key = f"local:{file_sha256}:{record_index if record_index is not None else 'all'}"
        else:
            file_sha256 = None
            record_index = None
            dedup_key = f"online:{query.casefold()}"
        with self._connect() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM recent WHERE dedup_key = ?", (dedup_key,))
            connection.execute(
                "INSERT INTO recent(dedup_key,kind,query,label,at_utc,file_sha256,record_index) VALUES(?,?,?,?,?,?,?)",
                (dedup_key, kind, query, label or query, _utcnow(), file_sha256, record_index),
            )
            connection.execute("DELETE FROM recent WHERE id NOT IN (SELECT id FROM recent ORDER BY id DESC LIMIT 20)")

    def list_recent(self, limit: int = 20) -> list[RecentEntry]:
        if type(limit) is not int or limit < 0:
            raise ValidationError("Recent limit must be a nonnegative integer")
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT dedup_key AS key,kind,query,label,at_utc,file_sha256,record_index FROM recent ORDER BY id DESC LIMIT ?",
                (min(limit, 20),),
            ).fetchall()
        return [RecentEntry(**dict(row)) for row in rows]

    def remove_recent(self, key: str) -> bool:
        with self._connect() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute("DELETE FROM recent WHERE dedup_key = ?", (key,))
            return cursor.rowcount > 0

    def add_favorite(self, snapshot: DataSnapshot, label: str | None = None) -> str:
        if snapshot.source_kind == "online":
            try:
                catalog = int(snapshot.payload["NORAD_CAT_ID"])
            except (KeyError, ValueError, TypeError) as exc:
                raise ValidationError("Online favorite needs a NORAD ID") from exc
            if catalog <= 0:
                raise ValidationError("Online favorite needs a positive NORAD ID")
            file_hash, record_index = None, None
            key = f"online:{catalog}"
        elif snapshot.source_kind == "local":
            file_hash, record_index = _source_reference(snapshot)
            key = f"local:{file_hash}:{record_index}"
        else:
            raise ValidationError("Unsupported favorite source kind")
        name = snapshot.payload.get("OBJECT_NAME")
        label = label.strip() if isinstance(label, str) else ""
        display = label or (name if isinstance(name, str) and name else key)
        encoded = _snapshot_json(snapshot)
        with self._connect() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM favorites WHERE key = ?", (key,))
            connection.execute(
                "INSERT INTO favorites(key,label,snapshot_json,at_utc,file_sha256,record_index) VALUES(?,?,?,?,?,?)",
                (key, display, encoded, _utcnow(), file_hash, record_index),
            )
        return key

    def list_favorites(self) -> list[FavoriteEntry]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT key,label,snapshot_json,at_utc,file_sha256,record_index FROM favorites ORDER BY id DESC"
            ).fetchall()
        return [FavoriteEntry(
            key=row["key"], label=row["label"], snapshot=DataSnapshot(**json.loads(row["snapshot_json"])),
            at_utc=row["at_utc"], file_sha256=row["file_sha256"], record_index=row["record_index"],
        ) for row in rows]

    def remove_favorite(self, key: str) -> bool:
        with self._connect() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute("DELETE FROM favorites WHERE key = ?", (key,))
            return cursor.rowcount > 0

    def clear_recent(self) -> None:
        with self._connect() as connection, connection:
            connection.execute("DELETE FROM recent")

    def clear_favorites(self) -> None:
        with self._connect() as connection, connection:
            connection.execute("DELETE FROM favorites")
