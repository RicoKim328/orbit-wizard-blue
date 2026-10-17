# SPEC Review Report: SPEC-DEPS-001
Iteration: 2/3
Verdict: PASS
Overall Score: 0.92 (harmonic mean; Tier S threshold 0.75; iteration 1 was 0.71, so no regression and no STOP)

Reasoning context ignored per M1 Context Isolation. Inputs read (Tier S contract): `spec.md` (v0.1.1), `plan.md`, plus `spec-compact.md` and `progress.md` for cross-reference. No `research.md` exists. Scope: regression check of iteration-1 defects D1-D7 plus a full regression pass over the four files.

## Must-Pass Results
- [PASS] MP-1 REQ number consistency: `### REQ-DEPS-001` (spec.md:L34), `-002` (L37), `-003` (L40), `-004` (L43), `-005` (L46), `-006` (L49). Sequential, no gaps or duplicates, 3-digit padding. ACs `AC-DEPS-001`..`007` at L56, L63, L72, L78, L85, L92, L98, also sequential.
- [PASS] MP-2 GEARS format compliance (judged on the REQ layer in spec.md §2 only; the Given-When-Then ACs in §3 are the verification layer and were not graded here): REQ-001/002/003 (L35, L38, L41) and REQ-005 (L47) are ubiquitous/unwanted ("shall not contain ... and shall keep"). REQ-004 (L44) is event-driven ("When a fresh Python 3.12 environment is built ..., the environment shall ..."). New REQ-006 (L50) is event-driven ("When a `.github/workflows/build.yml` run completes for the change's head commit, the `windows` job shall conclude `success`"). The iteration-1 `Where` clause is gone.
- [PASS] MP-3 YAML frontmatter validity: spec.md:L2-14 has all 12 canonical fields with correct types: `id: SPEC-DEPS-001`, `title` string, `version: "0.1.1"` (quoted, bumped from 0.1.0), `status: draft`, `created: 2026-10-17`, `updated: 2026-10-17`, `author: Rico`, `priority: P2`, `phase: "v0.1.1 target"`, `module: "pyproject.toml"`, `lifecycle: spec-anchored`, `tags` comma-separated string, plus `tier: S`. No rejected aliases. HISTORY row 0.1.1 (L24) records the iteration-1 fixes.
- [N/A] MP-4 Language neutrality: single-language (Python) project; the SPEC targets this repository's manifests, not template-bound content.
- [PASS] MP-5 D7 cross-SPEC reconciliation: `grep -Eoh 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+'` over all four files returns only `SPEC-DEPS-001` (6 occurrences, self). No BLOCKING finding.
- [PASS] MP-6 D8 cross-platform discipline: `grep -c syscall` = 0 in spec.md, plan.md, spec-compact.md, progress.md. Auto-PASS.
- [PASS] MP-7 clarification gate: `grep -rn 'NEEDS CLARIFICATION' .moai/specs/SPEC-DEPS-001/` exit 1 (no matches). `research.md` absent (Tier S).

## AC executability (each command run)

Scratch setup (outside the repository, no git): the tracked top-level content (`AGENTS.md assets LICENSES.txt orbit-wizard-blue.spec packaging pyproject.toml README.md requirements-dev.txt requirements.txt src tests tools`) was copied to `/tmp/deps-audit2-copy`, and the planned deletions were applied there: `pyproject.toml` L21, `requirements.txt` L4,5,6,17,22, `LICENSES.txt` L12. `diff` against unedited copies in `/tmp/deps-audit2-orig` showed exactly those seven lines removed. `$PY312` = `/home/rico/Desktop/Project/orbit-wizard-blue/.venv/bin/python3.12` (exists; `which python python3.12` finds nothing on PATH, which matches spec.md:L54).

Content checks (plan.md §F task 5), run verbatim in `/tmp/deps-audit2-copy`:

| AC bullet | Observed on edited copy | Negative control on original files |
|---|---|---|
| AC-001 count + no-requests (L58-59) | prints `9`, rc=0 | prints `10`, `AssertionError`, rc=1 |
| AC-001 exact nine-entry list (L60) | rc=0 | `AssertionError: [... 'platformdirs==4.4.0', 'requests==2.32.5']` |
| AC-002 no removed pin (L65-66) | `exit=1` only | prints L4, 5, 6, 17, 22 |
| AC-002 pin count (L67) | `16` | `21` |
| AC-002 header (L68) | `# Pinned Python 3.12 runtime packages, including transitive dependencies.` | same |
| AC-003 no Requests row (L74-75) | `0` | `1` |
| AC-006 no `import requests` (L96) | run in the worktree (the deletions do not touch `src tests tools`): `exit=1` only. Positive control with `urllib\b` returns data.py:15-17, so the pattern is not vacuous | n/a |

Fresh-environment checks (task 6), venv `/tmp/deps-audit2-venv` built with `$PY312 -m venv`, then `pip install -r requirements-dev.txt` (rc 0) and `pip install --no-deps -e .` (rc 0) from the edited copy:

| AC bullet | Observed |
|---|---|
| AC-004 `pip check` | `No broken requirements found.`, rc=0 |
| AC-004 `pip show` of the five | `WARNING: Package(s) not found: certifi, charset-normalizer, idna, requests, urllib3` / `exit=1` |
| AC-004 `find_spec` one-liner | rc=0 |
| AC-005 `--smoke-test` (offscreen) | `Smoke OK: Qt 6.9.3, PyQtGraph 0.13.7, PyOpenGL 3.1.10, Astropy 7.1.0`, rc=0 |
| AC-005 `ruff check src tests tools` | `All checks passed!`, rc=0 (run with `--no-cache` added so no cache file is written) |
| AC-005 `pytest -q` (offscreen, 3D disabled) | `169 passed, 4 warnings`, rc=0 (run with `-p no:cacheprovider` added) |

Commit-range checks (task 8). These need the run-phase commit, which does not exist, and the worktree guard refuses git operations outside the worktree, so they were simulated with `git diff --no-index` run from the worktree on the scratch files:

| AC bullet | Simulated output |
|---|---|
| AC-001 `--numstat` pyproject (L61) | `0	1	…/pyproject.toml` (expected `0	1	pyproject.toml`) |
| AC-002 `--unified=0 … \| grep -E '^\+[^+]'` (L69) | `exit=1` only; the `+++ b/…` header is excluded by `[^+]` |
| AC-002 `--numstat` requirements (L70) | `0	5	…/requirements.txt` |
| AC-003 `--numstat` LICENSES (L76) | `0	1	…/LICENSES.txt` |
| AC-006 `--name-only … -- . ':(exclude).moai'` (L94) | Pathspec syntax checked on real history: `git diff --name-only 6dd7167..HEAD -- . ':(exclude).moai'` prints nothing (commit 9491fb2 touches only `.moai/`), and `0861509..6dd7167` prints `tests/test_numerical.py`. So the exclude works and the check is not vacuous. Byte order puts `LICENSES.txt` before `pyproject.toml` and `requirements.txt`, which matches the listed order (L95) |

The expected strings in spec.md:L61, L70, L76 and spec-compact.md:L21, L25 contain real tab characters (`grep -P '\t'` / `cat -A` shows `0^I1^Ipyproject.toml`), so they match `--numstat` output byte for byte.

AC-007 (L99-103): `gh run list --json` lists `databaseId`, `status`, `conclusion` as valid fields. `gh run watch --help` has `--exit-status`. `build.yml` triggers on every `push` (build.yml:3-5) and has the single job `windows` (L8) with `--smoke-test` (L39) and `--gui-check` (L55) steps, so the run conclusion is the `windows` job conclusion. No run exists for the future head commit, so the AC was not executed. It is defined to be a Gap in that case.

Ordering: plan.md §F runs content checks in task 5 (L38) and fresh-env checks in task 6 (L39), commits in task 7 (L40), and runs every `<base_sha>..HEAD` bullet in task 8 (L41). spec.md §3 marks each commit-range bullet "after the run-phase commit" (L61, L69, L70, L76, L94) and spec-compact.md marks them "after commit" (L21, L23, L25, L29). `base_sha` is recorded in pre-flight step 2 (plan.md:L17), after the sync check in step 1 and before the first edit. progress.md has the §E.2 slot it names (progress.md:L8-10). The ordering is correct.

## Category Scores (0.0-1.0, rubric-anchored)
| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.75 | 0.75 | REQs are precise and counted (L35 "other nine entries", L38 "other sixteen pins", both confirmed). `<base_sha>` and `$PY312` are defined once (L54) and used the same way in the plan (L17-18) and compact (L5). Minor AC wording issue: AC-006's Given (L93) requires the commit, while its second bullet (L96) is a content check that the plan runs before the commit (D9) |
| Completeness | 1.0 | 1.0 | HISTORY L19-24, Context L26, Requirements L32, inline ACs L52, Exclusions with four `### Out of Scope — …` H3s and `-` bullets L105-121; frontmatter complete L2-14 |
| Testability | 1.0 | 1.0 | Every content and fresh-env bullet was run and gave the expected binary result. The negative controls fail as expected. The commit-range bullets were simulated with the expected output. AC-007 has defined PASS / wait / Gap outcomes (L101-103). No weasel words |
| Traceability | 1.0 | 1.0 | REQ-001→AC-001 (L56), 002→002 (L63), 003→003 (L72), 004→004/005 (L78, L85), 005→006 (L92), 006→007 (L98). Every REQ is covered, and every AC cites an existing REQ. The REQ-001 "versions unchanged" clause is now checked (L60, L61) |

Overall: harmonic mean 4 / (1/0.75 + 1 + 1 + 1) = 0.92 ≥ 0.75 (Tier S threshold).

## Defects Found (structured defect-list)
D8. COMPACT-PARAPHRASE-001 — spec-compact.md:L10, L12, L13 — The compact REQ lines paraphrase spec.md rather than quoting it. REQ-002 drops "with their versions" ("keep its header line and other sixteen pins unchanged" vs spec.md:L38 "its other sixteen pins with their versions unchanged"). REQ-004 says "ruff, and pytest" for "the ruff lint, and the pytest suite" (L44). REQ-005 drops "any file under" and "the application's" (L47). The meaning is the same, and spec-compact.md:L3 declares spec.md authoritative. REQ-001, 003 and 006 match spec.md verbatim. The AC table, files list and exclusions match spec.md and plan.md. — Severity: minor — Class: optional — Required fix (optional): copy the REQ-002, REQ-004 and REQ-005 sentences from spec.md:L38, L44, L47 verbatim into spec-compact.md:L10, L12, L13.

D9. AC006-GIVEN-001 — spec.md:L93 vs L96 — AC-DEPS-006's Given ("the run-phase commit(s) exist on top of the recorded `<base_sha>`") covers both bullets. The second bullet is marked "content check; needs no commit", and plan.md:L38 runs it in task 5, before the commit. A tester reading the Given literally would defer it. The result is the same either way. — Severity: minor — Class: optional — Required fix (optional): change L93 to "Given the change is applied (bullet 1 additionally requires the run-phase commit on top of `<base_sha>`)".

D10. AC007-NULL-001 — spec.md:L100-103 — When no run exists, the `--jq '.[0] | …'` expression prints `null null null` (checked: `echo '[]' | jq -r '.[0] | "\(.databaseId) \(.status) \(.conclusion)"'` → `null null null`). It does not print an empty line. The Gap rule on L103 still applies, and `null null null` cannot be mistaken for `completed success`. — Severity: minor — Class: optional — Required fix (optional): add "(the command prints `null null null`)" to L103.

No blocking defects.

## Regression Check (Iteration 2+ only)
Defects from previous iteration:
- D1 (bare `python` in AC-001): RESOLVED. spec.md:L58 and L60 use `"$PY312" -c`. `$PY312` is defined at L54 and plan.md:L18. Both commands ran with the expected result (above).
- D2 (working-tree `git diff` bullets): RESOLVED. spec.md:L69, L70, L76 now use `<base_sha>..HEAD`, are marked "after the run-phase commit", and give the result after the commit regardless of index state. Simulated output matches.
- D3 (AC-006 before commit): RESOLVED. plan.md task 5 (L38) has only content checks. New task 8 (L41) runs every commit-range bullet after the task 7 commit (L40). AC-006 bullet 1 is in task 8.
- D4 (`<base>` = merge base): RESOLVED. plan.md:L17 records `base_sha` via `git rev-parse HEAD` before the first edit into progress.md §E.2, and explicitly forbids a merge base. spec.md:L54 defines `<base_sha>` the same way. progress.md:L8-10 has the §E.2 slot.
- D5 (versions unchanged not checked): RESOLVED. spec.md:L60 asserts the exact nine-entry list in order with versions (fails on the original with the 10-entry list, passes on the edited copy). L61 adds `--numstat` `0	1	pyproject.toml`.
- D6 (optional, `Where` runtime condition): RESOLVED. The CI clause is now REQ-DEPS-006 (L49-50) in event-driven form. AC-DEPS-007 traces to it (L98). REQ-004 (L44) is a single sentence.
- D7 (optional, in-progress CI run): RESOLVED. spec.md:L100 adds `status` to the query. L102 says to wait with `gh run watch <run-id> --exit-status` and report a Gap until completion. Reflected in plan.md:L42 and spec-compact.md:L30.

No new blocking defect was introduced by the fixes. The deletion targets still match the tree (pyproject.toml:L21 `"requests==2.32.5",`; requirements.txt L4/5/6/17/22; LICENSES.txt L12). The removal-set decision in plan.md task 1 still holds: `pip show` in the primary `.venv` gives `Required-by: requests` for urllib3, certifi, idna and charset-normalizer.

## Recommendation
PASS. All must-pass criteria pass with cited evidence (MP-1 L34-50, MP-2 L35-50, MP-3 L2-14, MP-5/6/7 grep results). All seven iteration-1 defects are resolved. Every content-check and fresh-environment command runs as written against a scratch copy with the planned deletions and gives the expected result, and the negative controls on the original files fail. The commit-range checks are scheduled after the commit and produce the expected output in simulation. REQ-to-AC traceability is complete through REQ-DEPS-006. The score is 0.92 against the Tier S threshold of 0.75.

D8-D10 are optional wording fixes and can be left to the orchestrator.

Audit-time deviations to note: `ruff --no-cache` and `pytest -p no:cacheprovider` were added so no cache files were written. The commit-range bullets were simulated with `git diff --no-index` because no run-phase commit exists.

Scratch cleanup: this iteration's scratch paths (`/tmp/deps-audit2-copy`, `/tmp/deps-audit2-orig`, `/tmp/deps-audit2-venv`, two pip logs) were removed. Two directories from the iteration-1 audit still exist and were left untouched: `/tmp/deps-audit-s1` and `/tmp/deps-audit-scratch`.
