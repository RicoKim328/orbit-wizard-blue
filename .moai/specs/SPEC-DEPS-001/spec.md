---
id: SPEC-DEPS-001
title: "Remove unused requests dependency and its exclusive transitive pins"
version: "0.1.1"
status: completed
created: 2026-10-17
updated: 2026-10-17
author: Rico
priority: P2
phase: "v0.1.1 target"
module: "pyproject.toml"
lifecycle: spec-anchored
tags: "dependencies, packaging, requests, requirements, licenses, cleanup"
tier: S
---

# SPEC-DEPS-001: Remove unused requests dependency and its exclusive transitive pins

## HISTORY

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1.0 | 2026-10-17 | Rico | Initial draft (Tier S) |
| 0.1.1 | 2026-10-17 | Rico | Plan-audit iteration 1 fixes (D1-D7): `$PY312` in AC-DEPS-001; commit-range diff checks against a recorded `<base_sha>`; pyproject diff and full-list checks; CI clause moved to event-driven REQ-DEPS-006; in-progress CI run handling |

## 1. Context

orbit-wizard-blue declares `requests==2.32.5` as a runtime dependency (`pyproject.toml:21`) and pins it in `requirements.txt:17`, but no module in `src/`, `tests/`, `tools/`, `packaging/`, `orbit-wizard-blue.spec`, or `.github/` imports it. All HTTP goes through the standard library `urllib.request` (`src/orbit_wizard_blue/data.py:15-17`). In the current environment `requests` is required only by orbit-wizard-blue itself, and its four dependencies `urllib3`, `certifi`, `idna`, and `charset-normalizer` (pinned at `requirements.txt:22,4,6,5`) are required only by `requests`. `LICENSES.txt:12` names Requests as a bundled library. The project docs record this as a known risk (`.moai/project/tech.md:68`) and a roadmap candidate (`.moai/project/product.md:46`).

Removing the declaration, the five pins, and the license row makes the manifests match what the application actually uses, shrinks the reproducible environment, and stops the shipped notice from listing a library the build does not bundle.

## 2. Requirements (GEARS)

### REQ-DEPS-001 — Declared runtime dependencies
The `[project].dependencies` list in `pyproject.toml` shall not contain `requests`, and shall keep its other nine entries with their versions unchanged.

### REQ-DEPS-002 — Pinned runtime lock
The `requirements.txt` lock file shall not pin `requests`, `urllib3`, `certifi`, `idna`, or `charset-normalizer`, and shall keep its header line and its other sixteen pins with their versions unchanged.

### REQ-DEPS-003 — Third-party license notice
The `LICENSES.txt` notice shall not list Requests, and shall keep every other line unchanged.

### REQ-DEPS-004 — Reproducible environment integrity
When a fresh Python 3.12 environment is built from `requirements-dev.txt` followed by `pip install --no-deps -e .`, the environment shall report no broken requirements, shall contain none of the five removed distributions, and the application shall pass the offline smoke test, the ruff lint, and the pytest suite.

### REQ-DEPS-005 — Behavior and scope preservation
The change shall not modify any file under `src/`, `tests/`, `tools/`, `packaging/`, or `.github/`, nor `orbit-wizard-blue.spec`, `requirements-dev.txt`, or `README.md`, and the application's network access shall continue to go only through `urllib.request`.

### REQ-DEPS-006 — CI build
When a `.github/workflows/build.yml` run completes for the change's head commit, the `windows` job shall conclude `success`, including the frozen `--smoke-test` and `--gui-check` steps.

## 3. Acceptance Criteria (inline, Tier S)

Commands run from the repository root. `$SCRATCH` is a directory outside the repository (for example a job tmp dir). `$PY312` is a Python 3.12 interpreter (on the reference host, the primary checkout's `.venv/bin/python3.12`; bare `python` is not on PATH there). `<base_sha>` is the output of `git rev-parse HEAD` recorded in `progress.md` §E.2 before the first run-phase edit (plan.md §C). Bullets marked "after the run-phase commit" compare `<base_sha>..HEAD` and run only once the run-phase commit exists; all other bullets check file content and need no commit.

### AC-DEPS-001 — pyproject no longer declares requests (REQ-DEPS-001)
- Given the change is applied to `pyproject.toml`
- When `"$PY312" -c "import tomllib; d = tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; print(len(d)); assert not any(x.lower().replace('_','-').startswith('requests') for x in d)"` is run
- Then it prints `9` and exits 0
- And `"$PY312" -c "import tomllib; d = tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; assert d == ['PySide6==6.9.3', 'pyqtgraph==0.13.7', 'PyOpenGL==3.1.10', 'numpy==2.2.6', 'scipy==1.15.3', 'astropy==7.1.0', 'astropy-iers-data==0.2026.10.12.1.3.27', 'sgp4==2.24', 'platformdirs==4.4.0'], d"` exits 0 (the other nine entries keep their order and versions)
- And after the run-phase commit, `git diff --numstat <base_sha>..HEAD -- pyproject.toml` prints `0	1	pyproject.toml` (one line deleted, none added)

### AC-DEPS-002 — requirements.txt drops exactly the five pins (REQ-DEPS-002)
- Given the change is applied to `requirements.txt`
- When `grep -n -i -E '^(requests|urllib3|certifi|idna|charset[-_]normalizer)==' requirements.txt; echo "exit=$?"` is run
- Then it prints only `exit=1` (no matching line)
- And `grep -c -E '^[A-Za-z0-9_.-]+==' requirements.txt` prints `16`
- And line 1 is still `# Pinned Python 3.12 runtime packages, including transitive dependencies.`
- And after the run-phase commit, `git diff --unified=0 <base_sha>..HEAD -- requirements.txt | grep -E '^\+[^+]'; echo "exit=$?"` prints only `exit=1` (the diff only removes lines)
- And after the run-phase commit, `git diff --numstat <base_sha>..HEAD -- requirements.txt` prints `0	5	requirements.txt`

### AC-DEPS-003 — LICENSES.txt drops only the Requests row (REQ-DEPS-003)
- Given the change is applied to `LICENSES.txt`
- When `grep -c -i '^Requests:' LICENSES.txt` is run
- Then it prints `0`
- And after the run-phase commit, `git diff --numstat <base_sha>..HEAD -- LICENSES.txt` prints `0	1	LICENSES.txt`

### AC-DEPS-004 — Fresh environment has no broken or removed packages (REQ-DEPS-004)
- Given a fresh venv created with `"$PY312" -m venv "$SCRATCH/venv"` and populated with `"$SCRATCH/venv/bin/python" -m pip install -r requirements-dev.txt` followed by `"$SCRATCH/venv/bin/python" -m pip install --no-deps -e .`
- When `"$SCRATCH/venv/bin/python" -m pip check` is run
- Then it prints `No broken requirements found.` and exits 0
- And `"$SCRATCH/venv/bin/python" -m pip show requests urllib3 certifi idna charset-normalizer; echo "exit=$?"` reports none of the five packages found and ends with `exit=1`
- And `"$SCRATCH/venv/bin/python" -c "import importlib.util as u, sys; sys.exit(int(any(u.find_spec(m) for m in ('requests','urllib3','certifi','idna','charset_normalizer'))))"` exits 0

### AC-DEPS-005 — Application still works in the fresh environment (REQ-DEPS-004)
- Given the fresh venv from AC-DEPS-004
- When `QT_QPA_PLATFORM=offscreen "$SCRATCH/venv/bin/python" -m orbit_wizard_blue --smoke-test` is run
- Then it exits 0
- And `"$SCRATCH/venv/bin/python" -m ruff check src tests tools` exits 0
- And `QT_QPA_PLATFORM=offscreen ORBIT_WIZARD_DISABLE_3D=1 "$SCRATCH/venv/bin/python" -m pytest -q` exits 0 with 0 failed and 0 errors

### AC-DEPS-006 — Change scope is limited to three files (REQ-DEPS-005)
- Given the run-phase commit(s) exist on top of the recorded `<base_sha>`
- When, after the run-phase commit, `git diff --name-only <base_sha>..HEAD -- . ':(exclude).moai'` is run
- Then it prints exactly `LICENSES.txt`, `pyproject.toml`, `requirements.txt`
- And `git grep -n -E '^\s*(import|from)\s+requests\b' -- src tests tools; echo "exit=$?"` prints only `exit=1` (content check; needs no commit)

### AC-DEPS-007 — CI build passes (REQ-DEPS-006)
- Given the change is pushed and a `build.yml` run exists for its head commit `<head-sha>`
- When `gh run list --workflow build.yml --commit <head-sha> --json databaseId,status,conclusion --jq '.[0] | "\(.databaseId) \(.status) \(.conclusion)"'` is run
- Then it prints `<run-id> completed success`
- If the run exists but its status is not `completed`, wait for it (`gh run watch <run-id> --exit-status`), then re-run the command above and report the final conclusion; until it completes, the criterion is a Gap, not a pass.
- If no run exists for `<head-sha>`, the criterion is reported as a Gap, not a pass.

## 4. Exclusions

### Out of Scope — Source and test code
- No change to any module under `src/`, `tests/`, or `tools/`. The `requests` identifiers in `tests/test_data.py`, `tests/test_integration.py`, and `tests/test_local_integration.py` are local list variables, not the library, and stay as they are.
- No change to the HTTP layer (`urllib.request` in `src/orbit_wizard_blue/data.py`), the User-Agent string, timeouts, or TLS/CA handling.

### Out of Scope — Other dependency hygiene
- No change to the other `requirements.txt` pins (`packaging`, `PyYAML`, `typing_extensions`, `pyerfa`, `platformdirs`, and the rest), and no version bumps.
- No promotion of `pyerfa` into `pyproject.toml` despite the direct `erfa` import (a separate Known Risk).
- No change to `requirements-dev.txt`, `orbit-wizard-blue.spec`, `packaging/`, or `.github/workflows/build.yml`.

### Out of Scope — Other roadmap candidates
- No Linux CI job, no `MainWindow` split, no move of `gui_validation.py`; these are separate roadmap candidates in `.moai/project/product.md`.

### Out of Scope — Historical records
- `.moai/reports/plan-audit/PROJECT-review-1.md` stays as written; it is a dated audit record.
- `.moai/project/codemaps/data-flow.md:29` is not edited; there "requests" is a verb, not the library.
