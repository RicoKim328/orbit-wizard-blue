# Tech: orbit-wizard-blue

## Stack (pinned in `pyproject.toml` / `requirements.txt`)

| Package | Version | Role |
|---|---|---|
| Python | >=3.12,<3.13 | runtime (CI uses 3.12) |
| PySide6 | 6.9.3 | Qt GUI, `QThread` workers |
| pyqtgraph | 0.13.7 | 2D ground track and 3D OpenGL view |
| PyOpenGL | 3.1.10 | OpenGL backend for pyqtgraph.opengl |
| numpy | 2.2.6 | arrays (read-only results) |
| scipy | 1.15.3 | `solve_ivp` for manual propagation |
| astropy | 7.1.0 | time scales, TEME/GCRS/ITRS transforms, IERS |
| astropy-iers-data | 0.2026.10.12.1.3.27 | bundled IERS data |
| pyerfa | 2.0.1.5 | ERFA; pinned only in `requirements.txt` (transitive via astropy) although `orbit.py:14` imports `erfa` directly |
| sgp4 | 2.24 | SGP4 propagation, OMM/TLE handling |
| platformdirs | 4.4.0 | cache / data / log directories |
| requests | 2.32.5 | declared, not imported (see Known Risks) |

Rationale: exact pins plus pinned transitive deps in `requirements.txt` support deterministic results and reproducible PyInstaller builds. HTTP uses the standard library `urllib.request`.

Dev (`requirements-dev.txt`): pytest 8.4.2, pytest-qt 4.5.0, ruff 0.13.3, pyinstaller 6.16.0, pyinstaller-hooks-contrib 2026.8, setuptools 84.0.0.

## Development Environment

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m orbit_wizard_blue
```

On Windows, create the venv with `py -3.12 -m venv .venv` (README.md:58) and replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

## Commands

| Purpose | Command |
|---|---|
| Lint | `.venv/bin/python -m ruff check src tests tools` |
| Test | `QT_QPA_PLATFORM=offscreen ORBIT_WIZARD_DISABLE_3D=1 .venv/bin/python -m pytest -q` |
| Smoke test (builds a `QApplication`, `__main__.py:69`; on display-less Linux prefix `QT_QPA_PLATFORM=offscreen`) | `.venv/bin/python -m orbit_wizard_blue --smoke-test [--smoke-output FILE]` |
| GUI check (needs graphics context) | `.venv/bin/python -m orbit_wizard_blue --gui-check --gui-check-output-dir DIR` |
| Windows build | `.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm orbit-wizard-blue.spec` |

Ruff: `line-length = 110`, `target-version = "py312"`, `select = ["E4", "E7", "E9", "F"]`. Pytest: `testpaths = ["tests"]`, `pythonpath = ["src"]`.

## Environment Variables

| Variable | Effect |
|---|---|
| `ORBIT_WIZARD_DISABLE_3D=1` | `OrbitView` skips OpenGL (`gui/orbit_view.py:31`) |
| `ORBIT_WIZARD_LOG_DIR` | overrides log directory (`__main__.py:24`) |
| `QT_QPA_PLATFORM=offscreen` | headless Qt for tests |
| `QT_OPENGL=software` | Qt software OpenGL (used in CI GUI check) |

## Packaging

`orbit-wizard-blue.spec` builds a one-directory Windows app from `src/orbit_wizard_blue/__main__.py`. It collects astropy, astropy_iers_data, pyqtgraph and package data, copies dist metadata, adds `pyqtgraph.opengl` and filtered `OpenGL` submodules plus `gl_software_win32` on Windows, uses `packaging/hooks`, and aborts if `astropy.visualization` leaks into the analysis.

## CI (`.github/workflows/build.yml`)

Single job `windows` on `windows-latest`, triggered on push and `workflow_dispatch`: create venv, install pinned deps, ruff lint, pytest (offscreen, 3D disabled), PyInstaller build, frozen `--smoke-test` (expects `status: ok`), frozen `--gui-check` at `QT_SCALE_FACTOR` 1 / 1.5 / 2 with `QT_OPENGL=software`, upload diagnostics, add README and LICENSES, ZIP `orbit-wizard-blue-windows-x64.zip` as artifact.

## Known Risks

| Risk | Evidence |
|---|---|
| `requests` declared but unused; HTTP uses `urllib` | `pyproject.toml` dependencies; `data.py:15-17` imports `urllib`; no `import requests` in `src/` |
| Hardcoded User-Agent version differs from package version | `data.py:401` `orbit-wizard-blue/1.0` vs `pyproject.toml` `version = "0.1.0"` |
| `MainWindow` mixes many concerns in one file | `gui/window.py` 919 lines, single class from line 44 |
| Verification code ships in the runtime package | `src/orbit_wizard_blue/gui_validation.py` (321 lines) |
| Narrow lint scope, no type checker | `pyproject.toml` ruff `select = ["E4","E7","E9","F"]` (no E501, no `I`); no mypy/pyright config |
| CI is Windows-only while Linux/macOS dev is documented | `build.yml` `runs-on: windows-latest`; README line 64 "Linux/macOS" |
| 3D path is only exercised by the frozen Windows GUI check | tests run with `ORBIT_WIZARD_DISABLE_3D=1`; 3D runs only in the CI `--gui-check` step |
| `data.py` mutates `iers.conf` without `_EARTH_LOCK` used in `orbit.py` | `data.py:161-165`, `data.py:274` (also `orbit.py:29` at import time) vs `orbit.py:26`, `orbit.py:96-121` |
| `pyerfa` imported directly but not declared in `pyproject.toml` | `orbit.py:14` `import erfa`; only `requirements.txt` pins it |
| `AGENTS.md` says there is no Git history (stale) | `AGENTS.md:35` |
