# SPEC Review Report: PROJECT (project documents, .moai/project/)
Iteration: 2/3
Verdict: FAIL
Overall Score: 0.86

Reasoning context ignored per M1 Context Isolation. Audited artifacts: `.moai/project/product.md` (49 lines), `structure.md` (88), `tech.md` (77), `codemaps/overview.md` (29), `codemaps/modules.md` (27), `codemaps/dependencies.md` (47), `codemaps/data-flow.md` (42), `codemaps/entry-points.md` (27). Ground truth: `src/`, `tests/`, `tools/`, `pyproject.toml`, `requirements*.txt`, `.github/workflows/build.yml`, `README.md`.

Scope: the four prior blocking defects (D1-D4), the status of the optional defects (D5-D10), and a regression pass over every document. The regression pass included the new dashed-edge graph in `dependencies.md` and the revised diagram in `data-flow.md`. As in iteration 1, these are project documents, not a SPEC, so MP-1/2/3 are N/A. The Tier L default threshold (0.85) applies because there is no `tier:` field.

## Must-Pass Results
- [N/A] MP-1 REQ number consistency: the documents contain no `REQ-` entries. This is not a SPEC.
- [N/A] MP-2 EARS/GEARS format compliance: there is no requirement layer and no verification layer (checked against the requirement layer: zero REQ entries).
- [N/A] MP-3 YAML frontmatter validity: the SPEC frontmatter schema does not bind `.moai/project/*.md`.
- [N/A] MP-4 language neutrality: the project uses one language (`pyproject.toml:10` `requires-python = ">=3.12,<3.13"`).
- [PASS] MP-5 D7 cross-SPEC reconciliation: `grep -rnoE 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+' .moai/project` found nothing (exit 1).
- [PASS] MP-6 D8 cross-platform discipline: `grep -rn syscall .moai/project` found nothing.
- [PASS] MP-7 clarification gate: `grep -rn 'NEEDS CLARIFICATION' .moai/project` found nothing.

## Regression Check (prior defects)
- **D1 PROJ-QT-BOUNDARY — RESOLVED.** The four fixed statements now match the import scan:
  - `structure.md:65`
  - `overview.md:3`
  - `overview.md:22`
  - `dependencies.md:7`

  Module-level PySide6 imports appear only under `gui/` (`gui/window.py:10-11`, `gui/workers.py:9`, `gui/tables.py:7-8`, `gui/orbit_view.py:8-9`, `gui/manual_input.py:7-8`, `gui/ground_track_view.py:11`). The function-local imports are at `__main__.py:59-60,158`, `gui_validation.py:77,84,157-158` and `gl_software_win32.py:18` (inside `_qt_software_library()`, which reads `PySide6.__file__` to find `opengl32sw.dll`). Core, compute, infra and output modules import no Qt.
- **D2 PROJ-GUI-DEPS — RESOLVED.** Every edge added to `structure.md:66` and the graph at `dependencies.md:42-44` resolves:
  - `window.py:290,709` → manual; `window.py:724` → orbit; `window.py:727` → numerical; `window.py:810` → export
  - `manual_input.py:167` → manual
  - `gui_validation.py:37,38,152,160` → models, orbit, gl_platform, gui.window

  I re-checked all 16 solid edges against the module-level imports, and all are correct. The legend at `dependencies.md:22` states the convention (solid = module-level, dashed = function-local).
- **D3 PROJ-FLOW-REQ — RESOLVED** for the `OrbitRequest` contract:
  - `data-flow.md:15` builds `REQ` from the date edits, matching `window.py:718`.
  - `REQ --> SGP4 & NUM` and `SNAP --> SGP4` match `orbit.py:221-224`.
  - `MI --> NUM` matches `numerical.py:212-215` and `__main__.py:107`.
  - `models.py:79-82` holds only `start_utc`, `end_utc` and `step_seconds`.

  The same diagram still has, or has newly gained, two errors (N1 and N2 below).
- **D4 PROJ-SMOKE-HEADLESS — RESOLVED, and now reproduced by this auditor.** `entry-points.md:16` and `tech.md:41` now say the smoke test builds a `QApplication` (`__main__.py:69`) and that a display-less Linux host needs `QT_QPA_PLATFORM=offscreen`. Observed runs with the main-checkout `.venv` and `PYTHONPATH=src`, with `DISPLAY`/`WAYLAND_DISPLAY` unset:
  - `QT_QPA_PLATFORM` unset: `exit=134` (SIGABRT). Stderr: "Available platform plugins are: vnc, minimal, linuxfb, wayland, … offscreen."
  - `QT_QPA_PLATFORM=offscreen`: `exit=0`. Output: `Smoke OK: Qt 6.9.3, PyQtGraph 0.13.7, PyOpenGL 3.1.10, Astropy 7.1.0` and `{"status": "ok"}`.
- D5 (optional) — RESOLVED. `modules.md:11,13` now list `resolve_satellite` (`data.py:202`) and `record_recent`, `clear_recent`, `clear_favorites` (`user_store.py:111,202,206`).
- D6 (optional) — RESOLVED, but the edit introduced N3. The function-local citations (`__main__.py:55-58,61`, `gl_platform.py:26,29`, `gui_validation.py:35,70,83`) all resolve.
- D7 (optional) — RESOLVED. `tech.md:15,76` cover the pin: `requirements.txt:10` has `pyerfa==2.0.1.5`, it is absent from `pyproject.toml:11-22`, and `orbit.py:14` has `import erfa`.
- D8 (optional) — RESOLVED. `tech.md:33` cites `README.md:58` `py -3.12 -m venv .venv`, which is verified.
- D9 (optional) — the wording was applied, but it is inaccurate (N4). The inaccurate wording was prescribed by the iteration-1 report itself.
- D10 (optional) — RESOLVED. `entry-points.md:26-27` match the docstrings and flags at `check_live_data.py:1,21` and `validate_orbit.py:1,126-127`.

Unchanged facts re-verified:
- All 24 package line counts and all 14 test line counts (`wc -l`).
- 104 test functions.
- Tool line counts 176/71/129.
- Runtime and dev pins (`pyproject.toml:11-22`, `requirements.txt`, `requirements-dev.txt`).
- CI facts (`build.yml:9,30,39,47,52`).
- Paths (`data.py:154`, `user_store.py:79,81`, `local_data.py:81-82`, `__main__.py:24`).
- `README.md:64` "Linux/macOS:".

## Category Scores (0.0-1.0, rubric-anchored)
| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.75 | 0.75 | Most statements are exact. Two overgeneralizations need interpretation: overview.md:23 "without Qt or I/O dependencies" (N4), and overview.md:29 stating a lock invariant that tech.md:75 contradicts (N5). |
| Completeness | 1.0 | 1.0 | All sections are present (product.md:3-49, structure.md:3-88, tech.md:3-77, five codemaps). |
| Testability | 0.75 | 0.75 | Nearly every claim is checkable and holds, and D4 is now reproduced. Four claims are false: data-flow.md:11-12 (N1), data-flow.md:14 (N2), dependencies.md:8 (N3), overview.md:23 (N4). |
| Traceability | 1.0 | 1.0 | Every explicit file:line citation in all eight files resolves to the cited content, and every drawn import edge exists in the code. The only gap is the absent `__main__` node (N6, optional), which `dependencies.md:47` partly covers in prose. |

Aggregate (harmonic mean): 4 / (1/0.75 + 1/1.0 + 1/0.75 + 1/1.0) = 0.857. This is above iteration 1 (0.80), so there is no score regression and no STOP signal. It also meets the 0.85 Tier L threshold. The verdict is still FAIL because two blocking defects remain unresolved (N1, N2), which is the same class as iteration-1 D3.

## Defects Found (structured defect-list)
N1. PROJ-FLOW-EARTH — .moai/project/codemaps/data-flow.md:L11-L12, L19 — The diagram attributes EarthData to the wrong source and draws it twice.
- Node `SNAP` is labelled `DataSnapshot + EarthData`, and both `DS --> SNAP` and `LDS --> SNAP` feed it. So the diagram says `LocalDataService` produces EarthData. It does not: `import_file`, `load_import` and `load_record` return only `DataSnapshot` (`local_data.py:90,116,139`). EarthData is built only by `DataService.get_earth_data` (`data.py:268-304`), and the GUI always gets it from `self.service.get_earth_data` (`gui/window.py:731,748`).
- The revision also added a separate `ED[EarthData]` node (L19) with no incoming edge. EarthData now appears in two nodes: one feeds only SGP4, and the other has no source.

Severity: minor. Class: blocking (factual error and internal inconsistency in the data-flow codemap; same class as iteration-1 D3). Required fix: rename L11's node to `SNAP[DataSnapshot]`, add `DS --> ED`, and keep `ED --> SGP4 & NUM` as the only EarthData path.

N2. PROJ-FLOW-RECENT — .moai/project/codemaps/data-flow.md:L14 — The edge label `manual_snapshot: provenance / recent items` is half false. Manual snapshots are never written to recent items:
- `UserStore.record_recent` rejects any kind other than `online_query`/`local_import` (`user_store.py:115-116`).
- Its only callers pass those two kinds (`gui/window.py:371,387,427`).

`manual_snapshot` provides provenance and the source status: it becomes `result.satellite` (`numerical.py:225`) and `self.snapshot` (`gui/window.py:296,714`). This wording came from the iteration-1 report's own prescribed fix, which was wrong; codex flagged it independently. Severity: minor. Class: blocking (factual error in the data-flow codemap). Required fix: change the label to `manual_snapshot: provenance / source status` and drop "recent items".

N3. PROJ-PYQTGRAPH-ROW — .moai/project/codemaps/dependencies.md:L8 — The row places `gui/orbit_view.py` among the module-level pyqtgraph importers. It imports pyqtgraph only inside `OrbitView.__init__` (`gui/orbit_view.py:36-37`); its module-level imports (`orbit_view.py:5-12`) contain no pyqtgraph. This error comes from the new module-level/function-local split added for D6. Severity: minor. Class: optional. Required fix: change the row to "`gui/ground_track_view.py`; function-local: `gui/orbit_view.py:36-37`, `__main__.py:57-58`".

N4. PROJ-COMPUTE-IO — .moai/project/codemaps/overview.md:L23 — "functions without Qt or I/O dependencies" is false for `orbit.py` and `numerical.py`. Both read reference files from disk:
- `orbit.py`: `_file_sha256` opens files (`orbit.py:165-167`), and `_earth_context` reads the IERS-A and leap-second files (`orbit.py:107-112`).
- `numerical.py`: hashes and reads them (`numerical.py:101,249-254`).

This wording was also prescribed by the iteration-1 report (D9), and codex flagged it independently. Severity: minor. Class: optional. Required fix: replace it with "no Qt, network or write I/O; `orbit` and `numerical` read local IERS/leap-second files named by `EarthData`".

N5. PROJ-LOCK-INVARIANT — .moai/project/codemaps/overview.md:L29 (also L23) — "astropy/ERFA state guarded by `orbit._EARTH_LOCK`" is stated as a cross-cutting invariant. The repo's own Known Risks row contradicts it (`tech.md:75`): `data.py:161-165,274` sets `iers.conf` without the lock. In addition, `orbit.py:29` sets `iers.conf.auto_download = False` at import time, outside the lock. Severity: minor. Class: optional. Required fix: scope the invariant to "computation contexts (`orbit._earth_context`, also used by `numerical`)" and point to tech.md:75 for the unguarded `DataService` writes.

N6. PROJ-MAIN-EDGES — .moai/project/codemaps/dependencies.md:L24-L45 — The graph now draws function-local edges for `gui.window`, `gui.manual_input` and `gui_validation`, but it has no `__main__` node. `__main__` has eight function-local internal imports:
- export, manual, models, numerical, orbit (`__main__.py:63-67`)
- gl_platform (`__main__.py:128`)
- gui_validation (`__main__.py:134`)
- gui (`__main__.py:160`)

`dependencies.md:47` covers only the compute calls, in prose. Severity: minor. Class: optional. Required fix: add `main[__main__] -.-> export & manual & models & numerical & orbit & gl_platform & gui_validation & window`, or state under the legend that the entry module is omitted.

N7. PROJ-GREP-CLAIM — .moai/project/codemaps/modules.md:L3 — The file claims its names were "verified by `grep "^class \|^def "`". That pattern cannot match the indented methods listed in the file, such as `DataService.search_satellites` at `data.py:167` and `UserStore.record_recent` at `user_store.py:111`. The listed names are correct; only the stated method is wrong. Severity: minor. Class: optional. Required fix: change the note to "class, function and public-method names verified by grep".

## Cross-Model Second Opinion
`mcp__moai__audit_multi` ran with the default backends (`audit_model` is unset under `.moai/config`). Overall convergence: `fail`. `disagreement_flag: true`.
- **codex (required):** the verdict field reads `pass`, but the body says "Verdict: fail — three factual discrepancies". It raised overview.md:23 (= N4), overview.md:29 (= N5) and data-flow.md:14 "recent items" (= N2). I verified all three in the code above.
- **glm (advisory):** inconclusive. No API key, so it failed open.

## Gaps (not observed)
- Lint, pytest, `--gui-check` and the PyInstaller build were not executed. Only the smoke test was run (D4).
- The race named in tech.md:75 was not exercised. The unlocked writes were verified only at the code level (`data.py:161-165,274`).
- I could not determine whether the `LDS --> SNAP[DataSnapshot + EarthData]` edge predates iteration 2, because no prior document version is available (git was not used). Either way, it is a defect now.

## Recommendation
FAIL. No must-pass criterion failed (MP-1..4 N/A, MP-5..7 PASS), and D1-D4 are all resolved with accurate claims and resolving citations. The aggregate rose to 0.857.

Two blocking defects remain, both in `codemaps/data-flow.md`, and each is a one-line fix:
1. N1: at L11, rename the node to `SNAP[DataSnapshot]`. Add the edge `DS --> ED`. Make `ED --> SGP4 & NUM` the only EarthData path.
2. N2: at L14, change the edge label to `manual_snapshot: provenance / source status`.

N3-N7 are optional and left to the orchestrator; N3 and N4 are one-line factual corrections and are cheap to include. The iteration-3 re-audit should cover only N1-N2, plus a regression check on any lines edited for N3-N7.
