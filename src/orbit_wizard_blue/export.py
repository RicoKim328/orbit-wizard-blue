"""CSV and audit metadata export for a frozen ephemeris result."""

from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
from datetime import timezone
from pathlib import Path
from typing import Any

from .models import OrbitResult, thaw_json


_HEADER = (
    "sample_index", "utc_iso8601", "satellite_name", "norad_id",
    "teme_x_km", "teme_y_km", "teme_z_km",
    "teme_vx_km_s", "teme_vy_km_s", "teme_vz_km_s",
    "itrs_x_km", "itrs_y_km", "itrs_z_km",
    "itrs_vx_km_s", "itrs_vy_km_s", "itrs_vz_km_s",
    "geodetic_lat_deg", "geodetic_lon_deg", "geodetic_height_km",
    "gcrs_x_km", "gcrs_y_km", "gcrs_z_km",
    "gcrs_vx_km_s", "gcrs_vy_km_s", "gcrs_vz_km_s",
)


def _vector(array: Any, index: int) -> list[float | str]:
    return ["", "", ""] if array is None else [float(x) for x in array[index]]


def _write_csv(path: Path, result: OrbitResult) -> None:
    satellite_name = result.satellite.payload.get("OBJECT_NAME", "")
    norad_id = result.satellite.payload.get("NORAD_CAT_ID", "")
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(_HEADER)
        for i, instant in enumerate(result.times_utc):
            writer.writerow((i, instant, satellite_name, norad_id,
                             *_vector(result.teme_position_km, i), *_vector(result.teme_velocity_km_s, i),
                             *_vector(result.itrs_position_km, i), *_vector(result.itrs_velocity_km_s, i),
                             *_vector(result.geodetic_deg_km, i), *_vector(result.gcrs_position_km, i),
                             *_vector(result.gcrs_velocity_km_s, i)))


def _metadata(result: OrbitResult) -> dict[str, Any]:
    satellite = result.satellite
    request = result.request
    return {
        "schema_version": 3,
        "native_frame": result.native_frame,
        "source": {
            "url": satellite.source_url,
            "kind": satellite.source_kind,
            "format": satellite.source_format,
            "metadata": thaw_json(satellite.source_metadata),
            "payload": thaw_json(satellite.payload),
            "sha256": satellite.sha256,
            "fetched_at": satellite.fetched_at,
            "checked_at": satellite.checked_at,
            "stale": satellite.stale,
            "warning": satellite.warning,
        },
        "request": {
            "start_utc": request.start_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "end_utc": request.end_utc.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "step_seconds": request.step_seconds,
        },
        "sample_count": len(result.times_utc),
        "first_sample_utc": result.times_utc[0] if result.times_utc else None,
        "last_sample_utc": result.times_utc[-1] if result.times_utc else None,
        "columns": list(_HEADER),
        "frames_available": {"TEME": result.teme_position_km is not None,
                             "ITRS": result.itrs_position_km is not None,
                             "GCRS": result.gcrs_position_km is not None,
                             "GCRS_velocity": result.gcrs_velocity_km_s is not None},
        "warnings": list(result.warnings),
        "provenance": thaw_json(result.provenance),
    }


def _temp_path(directory: Path, suffix: str) -> Path:
    handle, name = tempfile.mkstemp(prefix=".orbit-wizard-", suffix=suffix, dir=directory)
    os.close(handle)
    return Path(name)


def export_ephemeris(result: OrbitResult, path: Path) -> tuple[Path, Path]:
    """Write CSV (UTF-8 BOM) and companion JSON using one result snapshot.

    Both files are staged before replacing destinations. Existing destinations are
    backed up and restored if the second replacement fails.
    """
    csv_path = Path(path).with_suffix(".csv")
    json_path = csv_path.with_suffix(".json")
    directory = csv_path.parent
    if not directory.is_dir():
        raise FileNotFoundError(f"Export directory does not exist: {directory}")
    staged: list[Path] = []
    backups: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        csv_temp = _temp_path(directory, ".csv")
        staged.append(csv_temp)
        json_temp = _temp_path(directory, ".json")
        staged.append(json_temp)
        _write_csv(csv_temp, result)
        with json_temp.open("w", encoding="utf-8") as stream:
            json.dump(_metadata(result), stream, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
            stream.write("\n")
        for destination in (csv_path, json_path):
            if destination.exists():
                backup = _temp_path(directory, destination.suffix + ".bak")
                staged.append(backup)
                shutil.copy2(destination, backup)
                backups[destination] = backup
        for source, destination in ((csv_temp, csv_path), (json_temp, json_path)):
            os.replace(source, destination)
            replaced.append(destination)
        return csv_path, json_path
    except Exception:
        for destination in reversed(replaced):
            backup = backups.get(destination)
            if backup is None:
                destination.unlink(missing_ok=True)
            else:
                os.replace(backup, destination)
        raise
    finally:
        for item in staged:
            item.unlink(missing_ok=True)
