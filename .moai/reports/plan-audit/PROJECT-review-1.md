# SPEC Review Report: PROJECT (project documents, .moai/project/)
Iteration: 1/3
Verdict: FAIL
Overall Score: 0.80

Reasoning context ignored per M1 Context Isolation. Audited artifacts: `.moai/project/product.md` (49 lines), `structure.md` (88), `tech.md` (76), `codemaps/overview.md` (29), `codemaps/modules.md` (27), `codemaps/dependencies.md` (42), `codemaps/data-flow.md` (39), `codemaps/entry-points.md` (27). Ground truth: `src/`, `tests/`, `tools/`, `pyproject.toml`, `requirements*.txt`, `.github/workflows/build.yml`, `orbit-wizard-blue.spec`, `packaging/hooks/hook-astropy.py`, `README.md`, `AGENTS.md`.

Document-type adaptation: these are project documents, not a SPEC. They carry no REQ-XXX entries, no AC-XXX entries, and no SPEC frontmatter, so MP-1/MP-2/MP-3 do not apply (N/A below, with the reason stated). The rubric dimensions are applied as: Clarity = unambiguous statements; Completeness = coverage of product/structure/tech/codemap sections; Testability = every factual claim is checkable against code and holds; Traceability = file:line citations resolve to the cited content. No `tier:` field exists, so the Tier L default threshold (0.85, `spec-workflow.md:142`) applies.

## Must-Pass Results
- [N/A] MP-1 REQ number consistency: project documents contain no `REQ-` entries (`grep -rn 'REQ-' .moai/project` returns nothing). This is not a SPEC.
- [N/A] MP-2 EARS/GEARS format compliance: no requirement layer exists (layer checked: requirement layer, zero REQ entries). No verification layer either.
- [N/A] MP-3 YAML frontmatter validity: the SPEC 12-field schema binds `.moai/specs/*/spec.md`, not `.moai/project/*.md`. None of the audited files has frontmatter.
- [N/A] MP-4 Section 22 language neutrality: single-language project (Python 3.12, `pyproject.toml:10` `requires-python = ">=3.12,<3.13"`). Auto-pass.
- [PASS] MP-5 D7 cross-SPEC reconciliation: `grep -rnoE 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+' .moai/project` returns no matches. No referenced SPEC, so no BLOCKING finding.
- [PASS] MP-6 D8 cross-platform discipline: `grep -rn syscall .moai/project` returns no matches. D8-4 auto-pass.
- [PASS] MP-7 clarification gate: `grep -rn 'NEEDS CLARIFICATION' .moai/project` returns no matches. No plan.md/research.md exists; `interview.md` and `harness-spec.yaml` were also scanned.

## Verified Correct (evidence)
- **Package line counts** (structure.md:32-61): all 24 values match `wc -l` exactly. Examples: `data.py` 489, `orbit.py` 339, `gui/window.py` 919, `gui_validation.py` 321, `gui/__init__.py` 5, `gl_platform.py` 38.
- **Test line counts** (structure.md:75-88): all 14 match.
- **Test inventory** (structure.md:18): 14 files and 104 test functions. Verified with `grep -hE '^(async )?def test_' tests/*.py | wc -l` = 104.
- **Tools line counts** (entry-points.md:25-27): `capture_gui.py` 176, `check_live_data.py` 71, `validate_orbit.py` 129. All match.
- **Runtime pins** (tech.md:7-18): match `pyproject.toml:10-21` and `requirements.txt` (pyerfa 2.0.1.5 at `requirements.txt:10`).
- **Dev pins** (tech.md:22): match `requirements-dev.txt:2-13`.
- **Ruff and pytest config** (tech.md:45): matches `pyproject.toml:33-43`.
- **Commands** (tech.md:39-43): identical to `build.yml:27,32,34`, `README.md:76-78,93`, and `AGENTS.md:23`.
- **CI description** (tech.md:62): matches `build.yml:3-88`: push and workflow_dispatch triggers, `windows-latest`, scales 1/1.5/2, `QT_OPENGL=software`, `status -ne 'ok'` check, ZIP name.
- **Packaging description** (tech.md:58): matches `orbit-wizard-blue.spec:8-32`.
- **Citations that resolve correctly:**
  - `data.py:15-17` (urllib imports), `data.py:161-165` and `data.py:274` (`iers.conf` mutations), `data.py:401` (User-Agent `orbit-wizard-blue/1.0`)
  - `orbit.py:26` (`_EARTH_LOCK = RLock()`), `orbit.py:96-121` (save/restore of `iers.conf` inside the lock)
  - `__main__.py:24` (`ORBIT_WIZARD_LOG_DIR`), `__main__.py:122-126` (argparse flags)
  - `gui/orbit_view.py:31` (`ORBIT_WIZARD_DISABLE_3D`), `gui/window.py:44` (`class MainWindow`)
  - `AGENTS.md:35` ("no Git history"), `README.md:64` ("Linux/macOS:")
- **Constants and interfaces:**
  - `CACHE_SECONDS = 7200`, `TIMEOUT_SECONDS = 8` and `GP_URL` (`data.py:27-29`)
  - `MAX_FILE_BYTES = 20_000_000` (`local_data.py:21`)
  - `_MAX_INTEGRATION_SPAN_S = 3600.0` (`numerical.py:25`)
  - `schema_version: 3` (`export.py:51`); UTF-8 BOM via `utf-8-sig` (`export.py:36`)
  - TaskWorker signals (`gui/workers.py:15-18`)
  - Frozen dataclasses (`models.py:47,65,78,96`)
  - SQLite filename (`user_store.py:81`) and `imports/` directory (`local_data.py:82`)
- **Absence claims:**
  - `requests` is not imported anywhere in `src/`. The only grep hits are prose and local variables in tests/tools.
  - No mypy/pyright config file exists.

## Category Scores (0.0-1.0, rubric-anchored)
| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.75 | 0.75 | Most statements are precise and quantified (see Verified Correct). Two overgeneralizations need interpretation: overview.md:23 "pure functions; accept progress/cancel callables", and entry-points.md:16 "headless". |
| Completeness | 1.0 | 1.0 | Product (description, audience, features, use cases, out of scope, roadmap: product.md:3-49), structure (tree, package/GUI/test tables, boundaries: structure.md:3-88), tech (stack, env, commands, env vars, packaging, CI, risks: tech.md:3-76), and five codemaps are all present. |
| Testability | 0.75 | 0.75 | Nearly every claim is checkable and holds. But structure.md:65 states a claim as "Verified by import scan" and the claim is false (D1). The data-flow edge in data-flow.md:14 contradicts `models.py:79-82` (D3). |
| Traceability | 0.75 | 0.75 | All explicit file:line citations resolve correctly. The dependency graph traceability is incomplete: structure.md:66 and dependencies.md:24-39 omit real import edges (D2). |

Aggregate (harmonic mean): 4 / (1/0.75 + 1/1.0 + 1/0.75 + 1/0.75) = 0.80. This is below the Tier L default threshold of 0.85.

## Defects Found (structured defect-list)
D1. PROJ-QT-BOUNDARY — .moai/project/structure.md:L65 — The text says "Verified by import scan … `gl_software_win32.py` imports PyOpenGL only". That is false: `src/orbit_wizard_blue/gl_software_win32.py:18` has `import PySide6`, a function-local import inside `_qt_software_library()` used to locate `opengl32sw.dll`. The same false boundary appears in three more places:
- `codemaps/overview.md:L3`: "Lower layers never import Qt". The Platform layer sits below GUI in that file's diagram, and it imports PySide6.
- `codemaps/overview.md:L22`: "only layer importing PySide6 (besides `gui_validation.py`)". This also ignores `__main__.py:59-60,158`.
- `codemaps/dependencies.md:L7`: the PySide6 row omits `gl_software_win32.py`.

This is the interview's declared top documentation priority ("Architecture and module boundaries", interview.md:L18). Codex independently reported the same defect. — Severity: major — Class: blocking — Required fix: Change structure.md:65 to say that `gl_software_win32.py` imports PyOpenGL at module level and PySide6 inside `_qt_software_library()` (to locate Qt's software OpenGL DLL). Change overview.md:3 and :22 so they state that PySide6 is imported at module level only in `gui/*`, and function-locally in `__main__.py`, `gui_validation.py` and `gl_software_win32.py`. Add `gl_software_win32.py (function-local)` to the dependencies.md:7 PySide6 row.

D2. PROJ-GUI-DEPS — .moai/project/structure.md:L66 — The "Dependency direction" line gives `gui → (data, local_data, user_store, models, ground_track, gl_platform)`. It omits four modules that `gui` actually imports, all function-local:
- `manual`: `gui/window.py:290,709` and `gui/manual_input.py:167`
- `orbit`: `gui/window.py:724`
- `numerical`: `gui/window.py:727`
- `export`: `gui/window.py:810`

The internal-import graph in `codemaps/dependencies.md:L24-L39` has the same gaps: no `window → manual/orbit/numerical/export` edges, and no `manual_input → manual` edge. dependencies.md:42 only partially compensates in prose. Neither file shows the edges of `gui_validation`: models, orbit, gl_platform and `gui.window` (`gui_validation.py:37,38,152,160`). — Severity: major — Class: blocking — Required fix: Add `manual, orbit, numerical, export (function-local)` to the gui list in structure.md:66. Add the dashed or labelled function-local edges `window -.-> manual & orbit & numerical & export` and `manual_input -.-> manual` to the dependencies.md graph. Add a `gui_validation --> models & orbit & gl_platform & window` edge, or state explicitly that the graph shows module-level imports only.

D3. PROJ-FLOW-REQ — .moai/project/codemaps/data-flow.md:L13-L16 — The diagram routes `ManualOrbitInput --> DataSnapshot --> OrbitRequest --> compute`. This misstates the compute contract in three ways:
- `OrbitRequest` holds only the time grid (`models.py:79-82`: `start_utc`, `end_utc`, `step_seconds`). It is built from the date edits (`gui/window.py:718`), not from a snapshot.
- `compute_ephemeris(snapshot, request, earth_data, …)` takes the snapshot as its own argument (`orbit.py:221-224`).
- `compute_manual_ephemeris(manual, request, earth_data, …)` takes the `ManualOrbitInput` directly (`numerical.py:212-215`, `__main__.py:107`).

— Severity: minor — Class: blocking (factual error in a data-flow codemap) — Required fix: Draw `SNAP --> SGP4`, `MI --> NUM`, `REQ[OrbitRequest: start/end/step] --> SGP4 & NUM`, and `EarthData --> SGP4 & NUM`. Drop `SNAP --> REQ`. Keep `MI --> SNAP` only as the provenance/recent-items snapshot (`manual_snapshot`, `gui/window.py:714`).

D4. PROJ-SMOKE-HEADLESS — .moai/project/codemaps/entry-points.md:L16, tech.md:L41 — `--smoke-test` is described as a "headless distribution check without opening the GUI". But `smoke_test()` constructs a `QApplication` (`__main__.py:69`) and imports `pyqtgraph.opengl` (`__main__.py:58`), so a Qt platform plugin is required. Codex reports that on a display-less host with `QT_QPA_PLATFORM` unset the command aborted with exit -6, and that it passed with `QT_QPA_PLATFORM=offscreen`. That run was NOT reproduced by this auditor (no `.venv` in this worktree). The code-level basis is `__main__.py:69`. — Severity: minor — Class: blocking — Required fix: Reword the description to "opens no window (still initializes a Qt application)". In tech.md:41, add that a display-less Linux host needs `QT_QPA_PLATFORM=offscreen`.

D5. PROJ-IFACE-OMIT — .moai/project/codemaps/modules.md:L11, L13 — The file claims its names were "verified by grep", but the public interface lists omit several methods:
- `DataService.resolve_satellite` (`data.py:202`)
- `UserStore.record_recent` (`user_store.py:111`), the only writer of recent items
- `UserStore.clear_recent` (`user_store.py:202`)
- `UserStore.clear_favorites` (`user_store.py:206`)

— Severity: minor — Class: optional — Required fix: Add the four methods to the respective rows.

D6. PROJ-EXT-DEPS-ROWS — .moai/project/codemaps/dependencies.md:L8, L9, L12 — The external-package rows omit function-local importers, which is inconsistent with the PySide6 row that does list them:
- astropy: `__main__.py:55,61` and `gui_validation.py:35`
- pyqtgraph: `__main__.py:57-58`
- OpenGL: `__main__.py:56`, `gui_validation.py:70,83` and `gl_platform.py:26,29`

— Severity: minor — Class: optional — Required fix: Append "(function-local: …)" entries, or state that the table lists module-level importers only.

D7. PROJ-PYERFA-UNDECLARED — .moai/project/tech.md:L3, L15 — The stack table header reads "pinned in `pyproject.toml` / `requirements.txt`". That blurs the fact that `pyerfa` is pinned only in `requirements.txt:10` and is absent from `pyproject.toml:11-22`, while `orbit.py:14` imports `erfa` directly. The undeclared direct dependency is not listed under Known Risks. — Severity: minor — Class: optional — Required fix: Mark pyerfa as "requirements.txt only (transitive via astropy, imported directly)" and optionally add a Known Risks row.

D8. PROJ-WIN-VENV — .moai/project/tech.md:L27, L33 — The Windows note says only to replace the interpreter path. But `README.md:58` and `AGENTS.md:23` create the Windows venv with `py -3.12 -m venv .venv`, not `python3.12`. — Severity: minor — Class: optional — Required fix: Add "create the venv with `py -3.12 -m venv .venv` on Windows".

D9. PROJ-COMPUTE-PURE — .moai/project/codemaps/overview.md:L23 — The Compute layer is described as "pure functions; accept `progress`/`cancel` callables". Neither half holds for the whole layer:
- `validate_manual_input`, `manual_snapshot` (`manual.py:87,191`) and `ground_track_plot` (`ground_track.py:11`) take no progress/cancel.
- `orbit.py` mutates process-global astropy/ERFA state (`orbit.py:29`, `orbit.py:95-121`).

— Severity: minor — Class: optional — Required fix: Say "functions without Qt or I/O dependencies; `compute_ephemeris` and `compute_manual_ephemeris` accept `progress`/`cancel`; orbit.py touches global astropy state under `_EARTH_LOCK`".

D10. PROJ-TOOLS-DESC — .moai/project/codemaps/entry-points.md:L26-L27 — The tool purposes are vaguer than their docstrings:
- `check_live_data.py` is a "one-shot live source and 24-hour calculation check" with a required `--cache-dir` (`check_live_data.py:1,21`).
- `validate_orbit.py` is a "reproducible offline orbit fixture and 100,000-sample validation" with `--orbit meo|geo` and `--count` (`validate_orbit.py:1,126-127`).

— Severity: minor — Class: optional — Required fix: Use the docstring summaries and the required flags.

## Regression Check (Iteration 2+ only)
N/A: iteration 1.

## Cross-Model Second Opinion
`mcp__moai__audit_multi` ran with the default (`audit_model` is unset in `.moai/config`). The overall convergence verdict is `fail`.
- **codex (required):** the verdict field reads `pass`, but the body says "Verdict: fix". It confirms D1 (gl_software_win32.py:18) and raised D4.
- **glm (advisory):** inconclusive (no API key, fail-open).
- **Disagreement flag:** set, but it comes from codex's verdict field, not from its findings.

## Gaps (not observed)
- The documented commands were not executed (lint, pytest, smoke test, gui-check, PyInstaller). The worktree has no `.venv`, so they were checked only by comparing them to README, AGENTS and build.yml.
- The smoke-test abort in D4 is a codex observation that this auditor did not reproduce.
- The race described in tech.md:75 (Known Risks) is a hypothesis in the audited doc. The citations were verified; the race itself was not.

## Recommendation
FAIL. No must-pass criterion failed (MP-1..4 N/A, MP-5..7 PASS). The verdict is FAIL because there are four blocking correctness defects and the aggregate score of 0.80 is below the 0.85 Tier L default. The fixes are small and local:
1. D1: correct the Qt-boundary statements in structure.md:65, overview.md:3 and :22, and dependencies.md:7.
2. D2: complete the gui dependency edges in structure.md:66 and the dependencies.md graph, and state the module-level vs function-local convention.
3. D3: redraw data-flow.md:13-16 so `OrbitRequest` is a time-grid input next to the snapshot or the manual input.
4. D4: reword "headless" in entry-points.md:16 and add the `QT_QPA_PLATFORM=offscreen` note to tech.md:41.

D5-D10 are optional, at the orchestrator's discretion. The re-audit should be scoped to D1-D4 plus the regression check.
