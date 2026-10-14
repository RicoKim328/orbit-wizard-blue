"""One-shot live source and 24-hour calculation check.

Run from the repository root with the project environment:
    .venv/bin/python tools/check_live_data.py --cache-dir PATH [--output-dir PATH]

Use a fresh cache directory when validating provider connectivity. The script
does not retry requests or bypass CelesTrak's two-hour GP update policy.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, required=True, help="Persistent source-cache directory")
    parser.add_argument("--output-dir", type=Path, help="Optional CSV and metadata export directory")
    args = parser.parse_args()

    # A direct script invocation has tools/ on sys.path; use the local src tree.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from orbit_wizard_blue.data import DataService
    from orbit_wizard_blue.export import export_ephemeris
    from orbit_wizard_blue.models import OrbitRequest
    from orbit_wizard_blue.orbit import compute_ephemeris

    service = DataService(cache_dir=args.cache_dir)
    satellite = service.get_satellite("25544")
    earth = service.get_earth_data()
    start = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    request = OrbitRequest(start, start + timedelta(hours=24), 60)
    result = compute_ephemeris(satellite, request, earth)
    repeat = service.resolve_satellite(satellite)

    summary = {
        "sample_count": len(result.times_utc),
        "transforms_available": result.itrs_position_km is not None and result.gcrs_position_km is not None,
        "library_versions": result.provenance["libraries"],
        "gp_source_url": satellite.source_url,
        "gp_epoch": satellite.payload.get("EPOCH"),
        "gp_stale": satellite.stale,
        "gp_fetched_at": satellite.fetched_at,
        "gp_checked_at": satellite.checked_at,
        "cache_recheck_unchanged": (repeat.fetched_at, repeat.checked_at) == (satellite.fetched_at, satellite.checked_at),
        "iers_kind": earth.provenance["iers"]["kind"],
        "leap_seconds_kind": earth.provenance["leap_seconds"]["kind"],
        "warnings": list(result.warnings),
    }
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        csv_path, metadata_path = export_ephemeris(result, args.output_dir / "iss_24h.csv")
        summary["csv_path"] = str(csv_path)
        summary["metadata_path"] = str(metadata_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if (
        len(result.times_utc) == 1441
        and summary["transforms_available"]
        and summary["cache_recheck_unchanged"]
        and not satellite.stale
        and summary["iers_kind"] == "downloaded"
        and summary["leap_seconds_kind"] == "downloaded"
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
