"""Validated, persistent imports of local GP JSON and TLE files."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from platformdirs import user_data_dir

from .models import DataSnapshot, ValidationError
from .tle import parse_tle
from .validation import gp_items


MAX_FILE_BYTES = 20_000_000
_HASH_PATTERN = re.compile(r"[0-9a-f]{64}")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _records(raw: bytes) -> tuple[str, list[tuple[dict[str, Any], dict[str, Any]]]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("Local file must be UTF-8 text") from exc
    stripped = text.lstrip()
    if stripped.startswith(("{", "[")):
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"GP JSON line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
        items = [value] if isinstance(value, dict) else value
        if not isinstance(items, list) or not items:
            raise ValidationError("GP JSON must contain at least one record")
        for index, item in enumerate(items):
            try:
                gp_items(json.dumps([item], ensure_ascii=False).encode())
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"GP JSON record #{index + 1}: {exc}") from exc
        return "gp_json", [(item, {}) for item in items]
    try:
        parsed = parse_tle(text)
    except ValidationError as exc:
        raise ValidationError(f"TLE import: {exc}") from exc
    records = []
    for index, record in enumerate(parsed):
        try:
            gp_items(json.dumps([record.payload]).encode())
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"TLE record #{index + 1}: {exc}") from exc
        records.append((record.payload, record.metadata))
    return "tle", records


class LocalDataService:
    """Copy complete, validated source files into the Windows user-data area."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else Path(user_data_dir("orbit-wizard-blue"))
        self.import_dir = self.data_dir / "imports"
        self.import_dir.mkdir(parents=True, exist_ok=True)

    def _paths(self, file_sha256: str) -> tuple[Path, Path]:
        if not _HASH_PATTERN.fullmatch(file_sha256):
            raise ValidationError("Invalid local file hash")
        return self.import_dir / f"{file_sha256}.source", self.import_dir / f"{file_sha256}.meta.json"

    def import_file(self, path: Path) -> list[DataSnapshot]:
        path = Path(path)
        try:
            with path.open("rb") as stream:
                raw = stream.read(MAX_FILE_BYTES + 1)
        except OSError as exc:
            raise ValidationError(f"Could not read local file {path.name}: {exc}") from exc
        if len(raw) > MAX_FILE_BYTES:
            raise ValidationError(f"Local file exceeds {MAX_FILE_BYTES} bytes")
        if not raw:
            raise ValidationError("Local file is empty")
        source_format, records = _records(raw)
        file_hash = sha256(raw).hexdigest()
        imported_at = _utcnow()
        source_path, meta_path = self._paths(file_hash)
        metadata = {
            "file_sha256": file_hash,
            "filename": path.name,
            "imported_at": imported_at,
            "source_format": source_format,
            "record_count": len(records),
        }
        _atomic_write(source_path, raw)
        _atomic_write(meta_path, json.dumps(metadata, ensure_ascii=False).encode())
        return self._snapshots(records, metadata)

    def load_import(self, file_sha256: str) -> list[DataSnapshot]:
        source_path, meta_path = self._paths(file_sha256)
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            with source_path.open("rb") as stream:
                raw = stream.read(MAX_FILE_BYTES + 1)
        except (OSError, ValueError) as exc:
            raise ValidationError("Stored local import is unavailable") from exc
        if not isinstance(metadata, dict):
            raise ValidationError("Stored local import metadata is invalid")
        if len(raw) > MAX_FILE_BYTES or sha256(raw).hexdigest() != file_sha256:
            raise ValidationError("Stored local import failed integrity check")
        source_format, records = _records(raw)
        if (
            metadata.get("file_sha256") != file_sha256
            or metadata.get("source_format") != source_format
            or metadata.get("record_count") != len(records)
            or not isinstance(metadata.get("filename"), str)
            or not isinstance(metadata.get("imported_at"), str)
        ):
            raise ValidationError("Stored local import metadata is invalid")
        return self._snapshots(records, metadata)

    def load_record(self, file_sha256: str, record_index: int) -> DataSnapshot:
        if type(record_index) is not int or record_index < 0:
            raise ValidationError("Record index must be a nonnegative integer")
        records = self.load_import(file_sha256)
        try:
            return records[record_index]
        except IndexError as exc:
            raise ValidationError("Local record index is out of range") from exc

    @staticmethod
    def _snapshots(
        records: list[tuple[dict[str, Any], dict[str, Any]]], metadata: dict[str, Any]
    ) -> list[DataSnapshot]:
        snapshots = []
        for index, (payload, record_metadata) in enumerate(records):
            canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            source_metadata = {**metadata, "record_index": index, **record_metadata}
            snapshots.append(DataSnapshot(
                payload=payload,
                source_url=f"local://{metadata['file_sha256']}/{index}",
                fetched_at=metadata["imported_at"],
                checked_at=metadata["imported_at"],
                sha256=sha256(canonical).hexdigest(),
                source_kind="local",
                source_format=metadata["source_format"],
                source_metadata=source_metadata,
            ))
        return snapshots
