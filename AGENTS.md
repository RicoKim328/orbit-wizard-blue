# Repository Guidelines

## Agent Roles & Coordination

The project name is `orbit-wizard-blue`. Astra is the primary coordinator: it plans with the user, assigns work, reviews and integrates results, and manages verification. Sub-agents perform application implementation when assigned.

The user has requested three sub-agents, all using `gpt-6-sol` with `medium` reasoning:

- `gui`: PySide6 GUI, result tables, embedded 3D orbit visualization, and playback controls.
- `backend_data`: CelesTrak data access, shared two-hour disk cache, manual refresh, and IERS/leap-second data management.
- `backend_orbit`: SGP4 propagation, UTC time grids, coordinate conversion, result models, and CSV/metadata export.

Only Astra may perform Git or GitHub operations. Sub-agents must not run `git` or `gh` commands (including read-only commands), access or modify `.git`, or perform repository operations through scripts, APIs, connectors, or other indirect methods. This includes staging, commits, branches, worktrees, fetch/pull/push, merges, tags, and pull requests. Ask Astra for any repository information or action needed.

Sub-agents must work within their assigned files, coordinate shared interfaces through Astra, and report changes, verification results, and blockers. Do not spawn additional agents or begin implementation without a concrete assignment from Astra. Agent setup and role acknowledgement alone do not authorize implementation.

## Project Structure & Module Organization

Application code lives in `src/orbit_wizard_blue/`: `data.py` handles external data/cache, `orbit.py` and `export.py` handle computation/export, `models.py` defines shared immutable data, and `gui/` contains PySide6 views. Tests live in `tests/`. The root README lists the entry point and file layout.

## Build, Test, and Development Commands

Use Python 3.12. From the repository root on Linux/macOS: `python3.12 -m venv .venv`, `.venv/bin/python -m pip install -r requirements-dev.txt`, `.venv/bin/python -m pip install --no-deps -e .`, `.venv/bin/python -m orbit_wizard_blue`. On Windows replace the Python path with `.venv\Scripts\python.exe` and create the environment with `py -3.12 -m venv .venv`. Lint with `.venv/bin/python -m ruff check src tests tools`; test with `QT_QPA_PLATFORM=offscreen ORBIT_WIZARD_DISABLE_3D=1 .venv/bin/python -m pytest -q`; build Windows onedir with `.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm orbit-wizard-blue.spec`. More detail is in the README.

## Coding Style & Naming Conventions

Python uses four-space indentation, `snake_case` for files/functions/variables, and `PascalCase` for classes. Ruff configuration lives in `pyproject.toml`. Keep formatting changes related to the task.

## Testing Guidelines

Pytest and pytest-qt are configured. Run the complete suite with `QT_QPA_PLATFORM=offscreen ORBIT_WIZARD_DISABLE_3D=1 .venv/bin/python -m pytest -q` on Linux/macOS, or set the same environment variables in PowerShell and run `.venv\Scripts\python.exe -m pytest -q` on Windows. Keep fixtures small and name tests after the behavior they verify. No coverage threshold is enforced.

## Commit & Pull Request Guidelines

There is no Git history available here, so no existing commit convention can be inferred. Use short, imperative commit subjects that describe the change, such as `Add project setup`. Pull requests should explain the purpose, summarize key changes, include verification commands and results, and link relevant issues. Include screenshots when a change affects a visual interface.
