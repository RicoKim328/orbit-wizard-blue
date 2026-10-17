# Product: orbit-wizard-blue

## Description

orbit-wizard-blue (package `orbit_wizard_blue` 0.1.0, `pyproject.toml` description: "Korean satellite orbit desktop application") is a PySide6 desktop application that computes and visualizes satellite orbits. It propagates CelesTrak or locally imported GP/TLE elements with SGP4, or propagates a manually entered initial state numerically. Results appear as a table, a 3D orbit view, and a ground track, and can be exported to CSV with a metadata JSON. The user interface and README are in Korean.

Status: actively developed. Maintainer: solo.

## Target Audience

- Korean-speaking users who want to inspect a satellite's ephemeris on a Windows desktop without installing Python (portable PyInstaller build).
- Users who need reproducible, offline-capable results (bundled IERS data, cached provider data, deterministic smoke test).

## Core Features

| Feature | Implementation |
|---|---|
| Satellite search and fetch from CelesTrak GP API (by name or NORAD catalog number) | `data.py` `DataService.search_satellites` / `get_satellite` |
| 2-hour disk cache with ETag / If-Modified-Since revalidation, throttle and failure records | `data.py` (`CACHE_SECONDS = 7200`) |
| IERS-A and leap-second reference data management (no implicit astropy network access) | `data.py` `get_earth_data`, `orbit.py` `_earth_context` |
| Local GP JSON / TLE file import (20 MB limit) | `local_data.py` `LocalDataService`, `tle.py` |
| Recent items and favorites (SQLite) | `user_store.py` `UserStore` |
| SGP4 ephemeris in TEME, GCRS, ITRS and geodetic output | `orbit.py` `compute_ephemeris` |
| Manual input: Keplerian elements or state vector, two-body or J2 gravity, constant acceleration, impact / periapsis events | `manual.py`, `numerical.py` `compute_manual_ephemeris` |
| Ground track plot with Natural Earth 110m coastline | `ground_track.py`, `gui/ground_track_view.py` |
| 3D orbit view (pyqtgraph OpenGL; can be disabled) | `gui/orbit_view.py` |
| CSV (UTF-8 with BOM) plus metadata JSON (schema version 3) export | `export.py` `export_ephemeris` |
| Background computation with progress and cancel | `gui/workers.py` `TaskWorker` |
| Distribution self-checks: `--smoke-test`, `--gui-check` | `__main__.py`, `gui_validation.py` |

## Use Cases

1. Search a satellite by name on CelesTrak, compute an ephemeris over a time range, review it in the table / 3D / ground-track views, and export CSV.
2. Work offline: reuse cached GP data, or import a local GP JSON / TLE file and compute with bundled IERS data.
3. Explore a hypothetical orbit by entering Keplerian elements or a state vector, optionally with J2 and constant acceleration.
4. Verify a portable Windows build with the frozen smoke test and GUI check.

## Out of Scope

Anything not implemented in code: other data sources than CelesTrak GP and local files, web or mobile versions.

## Roadmap Candidates (not committed)

These come from the code review behind this document. They are candidates only, not planned work.

- Add a Linux CI job (CI is Windows-only although Linux/macOS development is documented).
- Split `MainWindow` (`gui/window.py`, 919 lines) into smaller units.
- Move `gui_validation.py` out of the runtime package, or gate it behind the frozen-build check.
