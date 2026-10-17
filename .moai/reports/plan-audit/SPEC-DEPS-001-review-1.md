# SPEC Review Report: SPEC-DEPS-001
Iteration: 1/3
Verdict: FAIL
Overall Score: 0.71 (harmonic mean; Tier S threshold 0.75)

Reasoning context ignored per M1 Context Isolation. Inputs read (Tier S contract): `spec.md`, `plan.md`; also `progress.md` and `spec-compact.md` for cross-reference. No `research.md` exists.

## Must-Pass Results
- [PASS] MP-1 REQ number consistency: `### REQ-DEPS-001` (spec.md:L33), `-002` (L36), `-003` (L39), `-004` (L42), `-005` (L46). Sequential, no gaps, no duplicates, consistent 3-digit padding. ACs AC-DEPS-001..007 (L53, L58, L66, L72, L79, L86, L92) also sequential.
- [PASS] MP-2 GEARS format compliance (judged on the REQ layer in spec.md §2 only; the Given-When-Then ACs in §3 are the verification layer and were not graded here): REQ-001/002/003/005 are ubiquitous/unwanted ("shall not contain ... and shall keep", L34, L37, L40, L47). REQ-004 L43 is event-driven ("When a fresh Python 3.12 environment is built ..., the environment shall ..."); L44 is a `Where` clause. All match a pattern; see D6 for the `Where` usage note (optional).
- [PASS] MP-3 YAML frontmatter validity: spec.md:L2-14 carries all 12 canonical fields with correct types: `id: SPEC-DEPS-001`, `title` string, `version: "0.1.0"` (quoted), `status: draft` (in the 8-value enum, schema L71), `created: 2026-10-17`, `updated: 2026-10-17`, `author: Rico`, `priority: P2`, `phase: "v0.1.1 target"` (release target, not a lifecycle token), `module: "pyproject.toml"`, `lifecycle: spec-anchored`, `tags: "dependencies, packaging, ..."` (comma-separated string), plus `tier: S`. No rejected aliases.
- [N/A] MP-4 Language neutrality: single-language (Python) project; the SPEC targets this repository's manifests, not template-bound content.
- [PASS] MP-5 D7 cross-SPEC reconciliation: `grep -Eo 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+'` over spec.md and plan.md returns only `SPEC-DEPS-001` (self). No external SPEC references, so no BLOCKING finding.
- [PASS] MP-6 D8 cross-platform discipline: `grep -c syscall` = 0 in spec.md and plan.md. Auto-PASS.
- [PASS] MP-7 clarification gate: `grep -rn 'NEEDS CLARIFICATION' .moai/specs/SPEC-DEPS-001/` exit 1 (no matches). `research.md` absent (Tier S).

## Tree verification (claims vs real files)

All file/line claims in spec.md §1 and plan.md were checked against the worktree:

| Claim | Location | Observed |
|---|---|---|
| `requests==2.32.5` in dependencies | pyproject.toml:21 | `  "requests==2.32.5",` — confirmed; list has 10 entries (L12-21), so "other nine" is correct |
| pins `urllib3,certifi,idna,charset-normalizer` | requirements.txt:22,4,6,5 | L22 `urllib3==2.8.0`, L4 `certifi==2026.7.22`, L6 `idna==3.20`, L5 `charset-normalizer==3.5.2`; `requests==2.32.5` at L17. File has 21 pins, so 16 remain |
| Requests row | LICENSES.txt:12 | `Requests: Apache-2.0, https://requests.readthedocs.io/` |
| urllib imports | data.py:15-17 | `from urllib.error/parse/request import ...` |
| data.py:156,161,164-165,274,276-277,409 | src/orbit_wizard_blue/data.py | all match (opener=urlopen, auto_download=False, leap-second URLs "", `cache=False` opens, `self._opener(request, ...)`) |
| CI install steps | build.yml:22,24 | confirmed; single job `windows` (L8) |
| copy_metadata list | orbit-wizard-blue.spec:10 | confirmed, no requests |
| astropy certifi path | astropy/utils/data.py:1200-1203 | confirmed (`if "cafile" not in ssl_context and HAS_CERTIFI: import certifi ... certifi.where()`) |
| Docs rows | tech.md:18, tech.md:68, product.md:46, codemaps/dependencies.md:16, data-flow.md:29 | all confirmed; data-flow.md:29 is the verb "requests" |
| Required-by graph | primary `.venv` `pip show` | requests Required-by `orbit-wizard-blue`; urllib3 / certifi / idna / charset-normalizer each Required-by `requests` only; `pip check` = `No broken requirements found.` |

Import absence: `git grep -n -E '^\s*(import|from)\s+(requests|urllib3|certifi|idna|charset_normalizer)\b' -- src tests tools packaging orbit-wizard-blue.spec .github` → no output, `exit=1`. Positive control with the same regex shape (`urllib\b`) returns data.py:15-17, so the pattern is not vacuous. A plain substring grep finds only prose (gui_validation.py:20, check_live_data.py:7) and local `requests = []` list variables in tests/test_data.py, tests/test_local_integration.py, tests/test_integration.py, matching spec.md:L101. README.md has no hit.

## AC executability (each command run)

Simulation: the three files were copied to a scratch directory outside the repository (`/tmp/deps-audit-s1`) with the planned deletions applied (pyproject L21; requirements L4,5,6,17,22; LICENSES L12), plus `src/ tests/ tools/ assets/ README.md requirements-dev.txt`. A fresh venv was built at `/tmp/deps-audit-scratch/venv` from `/home/rico/Desktop/Project/orbit-wizard-blue/.venv/bin/python3.12`. git-based bullets could not be simulated (the worktree guard refuses git outside the worktree); their behavior is assessed from git semantics and flagged below.

| AC | Command (as written) | Observed | Result |
|---|---|---|---|
| 001 | `python -c "import tomllib; ..."` | bare `python`: `python: command not found`, rc=127. `/usr/bin/python3` is 3.10.12 (no `tomllib`). With `.venv/bin/python`: prints `9`, rc=0 | NOT executable as written (D1) |
| 002 b1 | `grep -n -i -E '^(requests|...)==' requirements.txt; echo "exit=$?"` | `exit=1` | OK |
| 002 b2 | `grep -c -E '^[A-Za-z0-9_.-]+==' requirements.txt` | `16` | OK |
| 002 b3 | line 1 | `# Pinned Python 3.12 runtime packages, including transitive dependencies.` | OK |
| 002 b4 | `git diff --unified=0 -- requirements.txt \| grep ...` | not run; working-tree-vs-index diff — empty once staged/committed, so the check passes vacuously | state-dependent (D2) |
| 003 b1 | `grep -c -i '^Requests:' LICENSES.txt` | `0` | OK |
| 003 b2 | `git diff --numstat -- LICENSES.txt` | not run; prints `0	1	LICENSES.txt` only while the edit is unstaged; prints nothing after `git add`/commit → FAIL on a correct implementation | state-dependent (D2) |
| 004 | `pip check` | `No broken requirements found.` exit=0 | OK |
| 004 | `pip show requests urllib3 certifi idna charset-normalizer; echo "exit=$?"` | `WARNING: Package(s) not found: certifi, charset-normalizer, idna, requests, urllib3` / `exit=1` | OK |
| 004 | `find_spec` one-liner | exit=0 | OK |
| 005 | `QT_QPA_PLATFORM=offscreen ... -m orbit_wizard_blue --smoke-test` | `Smoke OK: Qt 6.9.3, PyQtGraph 0.13.7, PyOpenGL 3.1.10, Astropy 7.1.0`, exit=0 | OK |
| 005 | `-m ruff check src tests tools` | `All checks passed!` exit=0 | OK |
| 005 | `... -m pytest -q` (run with `-p no:cacheprovider` added to avoid writing a cache) | `169 passed, 4 warnings`, exit=0 | OK |
| 006 b1 | `git diff --name-only <base>..HEAD -- . ':(exclude).moai'` | not run; empty if run before the commit, which is where plan.md:36 schedules it | ordering defect (D3, D4) |
| 006 b2 | `git grep ... requests\b -- src tests tools` | `exit=1` on current tree | OK |
| 007 | `gh run list --workflow build.yml --commit <sha> --json conclusion --jq '.[0].conclusion'` | `gh 2.82.1` supports `-c, --commit SHA`; origin is GitHub (`RicoKim328/orbit-wizard-blue`); run itself not available | executable; see D7 |

## Category Scores (0.0-1.0, rubric-anchored)
| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.75 | 0.75 | REQs are precise and counted ("other nine entries" L34, "other sixteen pins" L37, all confirmed). Ambiguity in the AC setup: the git state the diff checks assume is unstated (L64, L70), and `<base>` assumes a SPEC branch (L88) |
| Completeness | 1.0 | 1.0 | HISTORY L19, Context L25, Requirements L31, inline ACs L49, Exclusions with four `### Out of Scope — ...` H3s and `-` bullets L100-114; frontmatter complete L2-14 |
| Testability | 0.50 | 0.50 | 3 of 7 ACs fail or pass vacuously on a correct implementation depending on host or git state: AC-001 (bare `python`, rc 127), AC-002 b4 / AC-003 b2 (working-tree diff), AC-006 (scheduled before the commit). AC-004/005 verified executable and binary |
| Traceability | 0.75 | 0.75 | Every REQ has an AC (REQ-001→AC-001, 002→002, 003→003, 004→004/005/007, 005→006); no orphan ACs. The REQ-001 clause "with their versions unchanged" (L34) has no AC check (D5) |

Overall: harmonic mean 4 / (1/0.75 + 1/1.0 + 1/0.50 + 1/0.75) = 0.71 < 0.75 (Tier S threshold).

## Defects Found (structured defect-list)
D1. AC-EXEC-001 — spec.md:L55 — AC-DEPS-001 calls bare `python`. On the reference host `python` is not on PATH (`python: command not found`, rc 127) and `/usr/bin/python3` is 3.10.12, which has no `tomllib`. The spec defines `$PY312` (L51) but this AC does not use it. — Severity: major — Class: blocking — Required fix: replace `python -c "import tomllib; ..."` with `"$PY312" -c "import tomllib; ..."` (verified: with `.venv/bin/python` it prints `9` and exits 0 on the edited file).

D2. AC-STATE-001 — spec.md:L64, L70 — AC-DEPS-002 bullet 4 (`git diff --unified=0 -- requirements.txt`) and AC-DEPS-003 bullet 2 (`git diff --numstat -- LICENSES.txt`) compare the working tree to the index. After `git add` or the commit in plan.md:38, AC-003 bullet 2 prints nothing and FAILS on a correct implementation, and AC-002 bullet 4 passes vacuously. A sync-phase re-run therefore gets different results. — Severity: major — Class: blocking — Required fix: compare against a recorded base instead: `git diff --unified=0 <base>..HEAD -- requirements.txt | grep -E '^\+[^+]'; echo "exit=$?"` and `git diff --numstat <base>..HEAD -- LICENSES.txt` → `0	1	LICENSES.txt`, with `<base>` defined as in D4, and state that these bullets run after the run-phase commit.

D3. PLAN-ORDER-001 — plan.md:L36 vs L38 — Task 5 runs AC-DEPS-006 before task 7 creates the commit. AC-006 needs "the run-phase commit(s)" (spec.md:L87), so at task 5 `<base>..HEAD` lists no files and the AC fails. Tasks 5 and 7 also pull in opposite directions today: AC-002/003 diff bullets need an uncommitted state while AC-006 needs a committed one. — Severity: major — Class: blocking — Required fix: in plan.md §F keep only the content checks (AC-001, AC-002 bullets 1-3, AC-003 bullet 1, AC-006 bullet 2) in task 5, and add a task after task 7 that runs AC-006 bullet 1 plus the D2 diff bullets against `<base>..HEAD`.

D4. AC-BASE-001 — spec.md:L88 — `<base>` is "the branch's merge base with `main`". Under the default Tier S route (Hybrid Trunk main-direct, spec-workflow.md Route A) there is no SPEC branch: the merge base of `main` with itself is HEAD, so the diff is empty. On the current branch `WT-project-docs` the merge base is `6dd7167` and the extra commit `9491fb2` touches only `.moai/` (excluded), so it happens to work there. — Severity: minor — Class: blocking (the D2/D3 fix depends on it) — Required fix: add a pre-flight step in plan.md §C that records `git rev-parse HEAD` before the first run-phase edit into progress.md as `base_sha`, and define `<base>` in spec.md §3 as that recorded SHA.

D5. TRACE-001 — spec.md:L34 vs L55-56 — REQ-DEPS-001 requires the other nine entries to keep "their versions unchanged", but AC-DEPS-001 checks only the count (`9`) and the absence of `requests`, and AC-DEPS-006 checks only file names. A changed version on another entry passes every AC. — Severity: minor — Class: blocking — Required fix: add to AC-DEPS-001: `And git diff --numstat <base>..HEAD -- pyproject.toml prints 0	1	pyproject.toml` (one deleted line, no added line).

D6. GEARS-WHERE-001 — spec.md:L44 — `Where a CI run of build.yml is available for the change` uses `Where` for a runtime condition, not a capability gate or static config, and REQ-DEPS-004 holds two requirements in two sentences. Each sentence still matches a pattern, so MP-2 passes. — Severity: minor — Class: optional — Required fix (optional): move L44 to its own `REQ-DEPS-006` in event-driven form ("When a `build.yml` run completes for the change's head commit, the `windows` job shall conclude `success`, including the frozen `--smoke-test` and `--gui-check` steps.") and retrace AC-DEPS-007 to it.

D7. AC-007-INPROGRESS — spec.md:L94-96 — A run that exists but is still in progress gives `conclusion` = `""`, which is neither `success` nor the "no CI run" Gap case. — Severity: minor — Class: optional — Required fix (optional): add "If the run has not completed, report a Gap until it completes; do not report PASS."

## Regression Check (Iteration 2+ only)
N/A (iteration 1).

## Recommendation
FAIL. All must-pass criteria pass, and the factual base is accurate: every file and line reference, the "nine" and "sixteen" counts, the Required-by graph, and the import absence were confirmed against the tree. A fresh Python 3.12 venv with the planned deletions passes `pip check`, the `pip show`/`find_spec` absence checks, the smoke test, ruff, and pytest (169 passed). The plan is sound. The failure is in the verification layer: ACs that a correct implementation fails, or passes for nothing, depending on host and git state.

Fix instructions for manager-spec:
1. spec.md:L55 — use `"$PY312" -c` in AC-DEPS-001 (D1).
2. plan.md §C — add a step that records `base_sha` (`git rev-parse HEAD` before the first run-phase edit) into progress.md; spec.md:L88 — define `<base>` as that SHA (D4).
3. spec.md:L64, L70 — rewrite both git-diff bullets as `<base>..HEAD` diffs that run after the commit (D2).
4. spec.md AC-DEPS-001 — add the `git diff --numstat <base>..HEAD -- pyproject.toml` → `0	1	pyproject.toml` bullet (D5).
5. plan.md §F — split task 5 so the commit-range checks (AC-006 bullet 1 and the bullets from items 3-4) run after task 7 (D3).
6. Optional: D6 (move the CI clause into its own REQ), D7 (in-progress run handling).
7. Regenerate spec-compact.md after the edits so it matches spec.md.
