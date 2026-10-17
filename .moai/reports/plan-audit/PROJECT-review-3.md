# SPEC Review Report: PROJECT (project documents, .moai/project/)
Iteration: 3/3
Verdict: PASS
Overall Score: 0.92

Reasoning context ignored per M1 Context Isolation. Audited artifacts: `.moai/project/product.md` (49 lines), `structure.md` (88), `tech.md` (77), `interview.md` (25), `harness-spec.yaml` (18), `codemaps/overview.md` (29), `codemaps/modules.md` (27), `codemaps/dependencies.md` (48), `codemaps/data-flow.md` (43), `codemaps/entry-points.md` (27). Ground truth: `src/orbit_wizard_blue/`, `tests/`, `tools/`, `README.md`, `AGENTS.md`.

Scope: verification of iteration-2 defects N1-N7, a regression pass over the five edited files (data-flow.md, dependencies.md, overview.md, modules.md, tech.md), and a re-check of the remaining documents against source. These are project documents, not a SPEC, so MP-1/2/3 are N/A. With no `tier:` field the Tier L threshold (0.85) applies.

## Must-Pass Results
- [N/A] MP-1 REQ number consistency: no `REQ-` entries; not a SPEC.
- [N/A] MP-2 EARS/GEARS format compliance: no requirement layer and no verification layer (judged against the requirement layer: zero REQ entries).
- [N/A] MP-3 YAML frontmatter validity: the SPEC frontmatter schema does not bind `.moai/project/*.md`.
- [N/A] MP-4 language neutrality: single-language project (Python 3.12, `tech.md:7`).
- [PASS] MP-5 D7 cross-SPEC reconciliation: `grep -rnoE 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+|syscall|NEEDS CLARIFICATION' .moai/project` returned no match (exit 1).
- [PASS] MP-6 D8 cross-platform discipline: no `syscall` in the documents (same grep).
- [PASS] MP-7 clarification gate: no `[NEEDS CLARIFICATION` markers (same grep).

## Regression Check (Iteration 2 defects)
- **N1 PROJ-FLOW-EARTH — RESOLVED.** `data-flow.md:11` is now `DS --> SNAP[DataSnapshot]`, and `data-flow.md:13` `LDS --> SNAP` no longer implies EarthData. `data-flow.md:12` `DS -- get_earth_data --> ED[EarthData]` and `data-flow.md:20` `ED --> SGP4 & NUM` make up the only EarthData path. Source: `data.py:268-304` builds `EarthData`. `local_data.py:90,116,139` return only `DataSnapshot`. `gui/window.py:731,748` obtain earth data from `self.service.get_earth_data`. `compute_ephemeris` (`orbit.py:221-224`) and `compute_manual_ephemeris` (`numerical.py:212-215`) both take `earth_data: EarthData | None`.
- **N2 PROJ-FLOW-RECENT — RESOLVED.** `data-flow.md:15` now reads `manual_snapshot: provenance / source status`. Source: `gui/window.py:296,714` and `numerical.py:225,286` (snapshot becomes `result.satellite`). `record_recent` is called only with `online_query`/`local_import` (`gui/window.py:371,387,427`).
- **N3 PROJ-PYQTGRAPH-ROW — RESOLVED.** `dependencies.md:8` lists `gui/ground_track_view.py` as module-level, which matches `ground_track_view.py:10` `import pyqtgraph as pg`. It lists `gui/orbit_view.py:36-37` and `__main__.py:57-58` as function-local, which matches the import scan.
- **N4 PROJ-COMPUTE-IO — RESOLVED.** `overview.md:23` now says "no Qt, network or write I/O; `orbit` and `numerical` read local IERS/leap-second files named by `EarthData`". Every citation resolves. `orbit.py:107-112` checks `is_file()` and calls `IERS_A.read` / `_read_leaps`. `orbit.py:165-167` is `_file_sha256` opening the file `rb`. `numerical.py:101` and `numerical.py:249-254` hash the files, then enter `_earth_context`. A grep of `orbit.py numerical.py manual.py ground_track.py` for `open(|write|urlopen|socket|mkdir|unlink` found only the read-mode open at `orbit.py:167` and `setflags(write=False)` at `ground_track.py:44-45`. Neither is write I/O.
- **N5 PROJ-LOCK-INVARIANT — RESOLVED.** `overview.md:29` scopes the lock to "computation contexts (`orbit._earth_context`, also used by `numerical`)" and names the unguarded writes. Source: `orbit.py:26` `_EARTH_LOCK = RLock()`, `orbit.py:29` `iers.conf.auto_download = False` at import time, `data.py:161-165,274` with no lock, and `numerical.py:102,254` using `_earth_context`. This is now consistent with `tech.md:75`.
- **N6 PROJ-MAIN-EDGES — RESOLVED.** `dependencies.md:44` adds `main[__main__] -.-> export & manual & models & numerical & orbit & gl_platform & gui_validation & window`. Source: `__main__.py:63-67,128,134,160`. Line 160 imports `orbit_wizard_blue.gui`, which re-exports `MainWindow` from `.window` (`gui/__init__.py:3`), so the `window` target is accurate.
- **N7 PROJ-GREP-CLAIM — RESOLVED.** `modules.md:3` now reads "class, function and public-method names verified by grep". I spot-checked the methods: `data.py:167` `search_satellites`, `data.py:268` `get_earth_data`, `local_data.py:90,116,139`.
- **tech.md edit (L75) — no regression.** `data.py:161-165`, `data.py:274`, `orbit.py:29`, `orbit.py:26` and `orbit.py:96-121` all resolve to the described content.

Unchanged facts re-verified this iteration:
- Line counts: all 24 package files, all 14 test files and the 3 tool files match `wc -l` exactly (structure.md:32-61,75-88, entry-points.md:25-27).
- Test functions: 104 (structure.md:18).
- Function-local import sites: `__main__.py:55-61,158`, `gui_validation.py:35,70,77,83,84,157-158`, `gl_platform.py:26,29`, `gl_software_win32.py:18`.
- All 16 solid internal edges match the module-level imports.
- Individual citations: CLI flags at `__main__.py:122-125`, `__main__.py:24,69`, `data.py:15-17,401`, `gui/orbit_view.py:31`, `MainWindow` at `window.py:44`, `README.md:58,64` and `AGENTS.md:35`.

## Category Scores (0.0-1.0, rubric-anchored)
| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.75 | 0.75 | Statements are exact, with two minor readings a careful engineer would resolve consistently. O1: data-flow.md:15+17 has the dashed `MI -.-> SNAP` edge plus `SNAP --> SGP4`. O2: structure.md:69 "orbit.py serializes iers.conf changes". |
| Completeness | 1.0 | 1.0 | All sections are present: product.md:3-49 (incl. Out of Scope L38-40), structure.md:3-88, tech.md:3-77, five codemaps, interview.md and harness-spec.yaml. |
| Testability | 1.0 | 1.0 | Every factual claim checked this iteration holds against source (see Regression Check). No weasel wording. |
| Traceability | 1.0 | 1.0 | Every explicit file:line citation across the edited files resolves. Every drawn import edge (solid and dashed) exists in code, and the `__main__` node is now present. |

Aggregate (harmonic mean): 4 / (1/0.75 + 1 + 1 + 1) = 0.923. This is higher than iteration 2 (0.857), so there is no score regression and no STOP signal. It is at or above the 0.85 Tier L threshold.

## Defects Found (structured defect-list)
O1. PROJ-FLOW-MANUAL-SGP4 — .moai/project/codemaps/data-flow.md:L15,L17 — The diagram can be misread. The dashed `MI -. manual_snapshot .-> SNAP` edge combined with `SNAP --> SGP4` suggests a manual snapshot can reach `compute_ephemeris`. In code it never does: when manual input is active, `gui/window.py:725-738` returns `compute_manual_ephemeris(...)` before reaching the SGP4 branch at L739-749. The label "provenance / source status" limits the misreading, so this is ambiguity, not a false statement. — Severity: minor — Class: optional — Required fix: point the dashed edge at `RES` (e.g. `MI -. manual_snapshot: provenance .-> RES`), or add a note under the diagram that `SNAP --> SGP4` carries only CelesTrak/local snapshots.

O2. PROJ-STRUCT-LOCK-SCOPE — .moai/project/structure.md:L69 — "`orbit.py` serializes `iers.conf` changes and IERS table use with `_EARTH_LOCK`" is the same overgeneralization that N5 fixed in overview.md. `orbit.py:29` sets `iers.conf.auto_download = False` at import time, outside the lock. tech.md:75 and overview.md:29 already state this exception, so the documents stay consistent overall. — Severity: minor — Class: optional — Required fix: append "inside `_earth_context` (`orbit.py:92-121`); the import-time write at `orbit.py:29` and `DataService` writes are unguarded (see tech.md Known Risks)".

No blocking defects found.

## Cross-Model Second Opinion
`mcp__moai__audit_multi` ran with the default backends (`audit_model` is unset). Overall convergence: `pass`, `disagreement_flag: false`.
- **codex (required):** `pass`, no findings. It checked architecture, APIs, data flow, dependencies, CLI, storage paths, test counts and CI claims against source.
- **glm (advisory):** inconclusive. No API key, so it failed open.

## Gaps (not observed)
- Lint, pytest, `--smoke-test`, `--gui-check` and the PyInstaller build were not executed this iteration. The smoke-test headless behavior was reproduced in iteration 2 and the cited lines are unchanged (`__main__.py:69`).
- CI facts (`build.yml`) and the pins in `pyproject.toml` / `requirements*.txt` were not re-read this iteration. They were verified in iteration 2, and tech.md:3-22,60-62 are outside the edited lines.
- No prior document versions were diffed (git not used). The regression check therefore compares the current text to source rather than to the iteration-2 text.

## Recommendation
PASS. No must-pass criterion fails: MP-1..4 are N/A and MP-5..7 PASS with grep evidence. All seven iteration-2 defects (N1-N7) are resolved with accurate wording and citations that resolve. The five edited files show no regression, and the remaining documents still match source. The aggregate is 0.923, above the 0.85 threshold, and the codex backend concurs.

O1 and O2 are optional wording refinements left to the orchestrator. Neither is a false claim, and both are covered elsewhere in the document set: O1 by the edge label, O2 by tech.md:75 and overview.md:29.
