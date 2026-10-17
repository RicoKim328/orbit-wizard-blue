# Project Interview

## Stage A Round 1: Ownership, Purpose, and Goal
Question: What state will the project continue in going forward?
Answer: Active product being developed further
Domain: satellite-orbit-propagation (auto-populated from codebase analysis)
Goal: Keep developing orbit-wizard-blue as a desktop app that computes and visualizes satellite orbits (SGP4 from CelesTrak/local TLE and manual numerical propagation) with table, 3D, ground-track and CSV export output.

## Stage A Round 2: Constraints and Non-Goals
Question: Which hard constraints must the project respect?
Answer: Offline operation with deterministic results; Windows distribution (PyInstaller)
Constraints:
- Offline operation and deterministic results (smoke test, offline fixtures, no implicit astropy network access)
- Windows distribution via PyInstaller onedir build (software OpenGL compatibility)

## Stage A Round 3: Scope, Boundaries, and Documentation Priority
Question: Which aspect must the documentation capture most accurately, and what is out of scope?
Answer: Architecture and module boundaries; out-of-scope derived from code evidence
Scope: In scope: CelesTrak GP data with 2-hour cache, local GP JSON/TLE import, SGP4 ephemeris, manual Keplerian/state propagation (two-body or J2, constant acceleration), TEME/GCRS/ITRS/geodetic output, ground track, 3D view, CSV plus metadata JSON export. Out of scope: anything not implemented in code (other data sources, web or mobile versions).

## Stage B Round 4: Verification, Surfaces, and Sharing
Verification: .venv/bin/python -m ruff check src tests tools && QT_QPA_PLATFORM=offscreen ORBIT_WIZARD_DISABLE_3D=1 .venv/bin/python -m pytest -q
UI surface: has-ui
External systems: CelesTrak GP API, IERS and leap-second data hosts (astropy defaults), local filesystem (cache, user data, logs), local SQLite
Team sharing: solo
