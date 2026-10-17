# SPEC-DEPS-001 — Progress

## §E.1 Plan-phase Audit-Ready Signal

plan_status: audit-ready
plan_complete_at: 2026-10-17

## §E.2 Run-phase Evidence

base_sha: e7804319dd11d4b350a82113ffd473bff12396a8
run_commit: 650bce3 (3 files, 7 deletions)
PY312: primary checkout `.venv/bin/python3.12`; fresh venv built in the job tmp dir (outside the repository)

Baseline (primary .venv, before edits): `ruff check src tests tools` exit 0; `--smoke-test` exit 0 ("Smoke OK: Qt 6.9.3, PyQtGraph 0.13.7, PyOpenGL 3.1.10, Astropy 7.1.0"); pytest `169 passed, 4 warnings`.
Pre-flight: `git grep` for imports of requests/urllib3/certifi/idna/charset_normalizer in src, tests, tools, packaging, spec, .github → exit 1 (none). `pip show`: urllib3, certifi, idna, charset-normalizer each `Required-by: requests`; requests `Required-by: orbit-wizard-blue`.

| AC | Result | Evidence |
|---|---|---|
| AC-DEPS-001 | PASS | dependency count prints `9`, exit 0; exact nine-entry list assert exit 0; `git diff --numstat` → `0	1	pyproject.toml` |
| AC-DEPS-002 | PASS | removed-pin grep `exit=1`; 16 pins; line 1 header intact; no added lines (`exit=1`); `0	5	requirements.txt` |
| AC-DEPS-003 | PASS | `grep -c -i '^Requests:'` → `0`; `0	1	LICENSES.txt` |
| AC-DEPS-004 | PASS | fresh venv: `pip check` → "No broken requirements found." (exit 0); `pip show` of the five → "Package(s) not found" (exit 1); `find_spec` check exit 0 |
| AC-DEPS-005 | PASS | fresh venv: `--smoke-test` exit 0 (same line as baseline); `ruff check src tests tools` → "All checks passed!"; pytest `169 passed, 4 warnings` |
| AC-DEPS-006 | PASS | `git diff --name-only <base_sha>..HEAD -- . ':(exclude).moai'` → `LICENSES.txt`, `pyproject.toml`, `requirements.txt`; no `import requests` in src/tests/tools (`exit=1`) |
| AC-DEPS-007 | PASS | head commit ff11382 (evidence-only commit on top of run commit 650bce3); `gh run list --workflow build.yml --commit ff11382...` → `39035500794 completed success`; job `windows`: success |

## §E.3 Run-phase Audit-Ready Signal

run_status: audit-ready (AC-DEPS-001..007 PASS)
run_complete_at: 2026-10-17

## §E.4 Sync-phase Audit-Ready Signal

sync_status: audit-ready
sync_complete_at: 2026-10-17

Sync evidence (head be16add):
- Quality: `ruff check src tests tools` → All checks passed!; pytest `169 passed, 4 warnings`.
- Divergence: none. Run commit 650bce3 touched only `pyproject.toml`, `requirements.txt`, `LICENSES.txt` as planned (0 added, 7 deleted lines); no unplanned files or dependency changes.
- Docs updated: `.moai/project/tech.md` (removed requests row and Known Risks row), `.moai/project/product.md` (removed completed roadmap item), `.moai/project/codemaps/dependencies.md` (removed requests row).
- Skipped: CHANGELOG (none in repo), README (no requests mention), structure.md (no structural change), MX tags (no source changes).
- SPEC status: draft → completed (lifecycle spec-anchored; AC-DEPS-001..007 PASS).
