# SPEC-DEPS-001 (compact)

Auto-generated summary of `spec.md` v0.1.1 and `plan.md`: requirements, acceptance criteria, files to modify, exclusions. `spec.md` is authoritative.

`$PY312` = the primary checkout's `.venv/bin/python3.12`. `<base_sha>` = `git rev-parse HEAD` recorded in `progress.md` §E.2 before the first run-phase edit. "After commit" checks compare `<base_sha>..HEAD` and run only after the run-phase commit.

## Requirements

- **REQ-DEPS-001**: The `[project].dependencies` list in `pyproject.toml` shall not contain `requests`, and shall keep its other nine entries with their versions unchanged.
- **REQ-DEPS-002**: The `requirements.txt` lock file shall not pin `requests`, `urllib3`, `certifi`, `idna`, or `charset-normalizer`, and shall keep its header line and other sixteen pins unchanged.
- **REQ-DEPS-003**: The `LICENSES.txt` notice shall not list Requests, and shall keep every other line unchanged.
- **REQ-DEPS-004**: When a fresh Python 3.12 environment is built from `requirements-dev.txt` followed by `pip install --no-deps -e .`, the environment shall report no broken requirements, shall contain none of the five removed distributions, and the application shall pass the offline smoke test, ruff, and pytest.
- **REQ-DEPS-005**: The change shall not modify `src/`, `tests/`, `tools/`, `packaging/`, `.github/`, `orbit-wizard-blue.spec`, `requirements-dev.txt`, or `README.md`, and network access shall continue to go only through `urllib.request`.
- **REQ-DEPS-006**: When a `build.yml` run completes for the change's head commit, the `windows` job shall conclude `success`, including the frozen `--smoke-test` and `--gui-check` steps.

## Acceptance Criteria

| AC | Check | Pass condition | When |
|---|---|---|---|
| AC-DEPS-001 | `"$PY312" -c` `tomllib` load of `[project].dependencies`: count, then exact list | prints `9`; list equals the nine expected entries in order; exit 0 | before commit |
| AC-DEPS-001 | `git diff --numstat <base_sha>..HEAD -- pyproject.toml` | `0	1	pyproject.toml` | after commit |
| AC-DEPS-002 | `grep -n -i -E '^(requests\|urllib3\|certifi\|idna\|charset[-_]normalizer)==' requirements.txt`; pin count; line 1 | no match (exit 1); `16`; header unchanged | before commit |
| AC-DEPS-002 | `git diff --unified=0 <base_sha>..HEAD -- requirements.txt \| grep -E '^\+[^+]'`; `git diff --numstat <base_sha>..HEAD -- requirements.txt` | no added line (exit 1); `0	5	requirements.txt` | after commit |
| AC-DEPS-003 | `grep -c -i '^Requests:' LICENSES.txt` | `0` | before commit |
| AC-DEPS-003 | `git diff --numstat <base_sha>..HEAD -- LICENSES.txt` | `0	1	LICENSES.txt` | after commit |
| AC-DEPS-004 | fresh `$SCRATCH/venv`: `pip check`, `pip show` of the five, `find_spec` of the five | `No broken requirements found.`; none found (exit 1); `find_spec` script exit 0 | before commit |
| AC-DEPS-005 | fresh venv: `--smoke-test` (offscreen), `ruff check src tests tools`, `pytest -q` (offscreen, 3D disabled) | all exit 0; 0 failed, 0 errors | before commit |
| AC-DEPS-006 | `git grep` for `import requests` in `src tests tools` | no match (exit 1) | before commit |
| AC-DEPS-006 | `git diff --name-only <base_sha>..HEAD -- . ':(exclude).moai'` | exactly `LICENSES.txt`, `pyproject.toml`, `requirements.txt` | after commit |
| AC-DEPS-007 | `gh run list --workflow build.yml --commit <head-sha> --json databaseId,status,conclusion` | `<run-id> completed success`; in progress → wait (`gh run watch <run-id> --exit-status`) and report the final conclusion, Gap until complete; no run → Gap | after push |

## Files to Modify

Run phase:
- `pyproject.toml:21` — delete `"requests==2.32.5",`
- `requirements.txt:4,5,6,17,22` — delete certifi, charset-normalizer, idna, requests, urllib3 pins
- `LICENSES.txt:12` — delete the Requests row

Sync phase:
- `.moai/project/tech.md:18` — delete the `requests` dependency row
- `.moai/project/tech.md:68` — delete the `requests` Known Risks row
- `.moai/project/product.md:46` — delete the roadmap bullet
- `.moai/project/codemaps/dependencies.md:16` — delete the `requests` row

## Exclusions

### Out of Scope — Source and test code
- No change under `src/`, `tests/`, `tools/`; test-local `requests` variables stay.
- No change to the HTTP layer, User-Agent, timeouts, or TLS/CA handling.

### Out of Scope — Other dependency hygiene
- No change to other `requirements.txt` pins and no version bumps.
- No promotion of `pyerfa` into `pyproject.toml`.
- No change to `requirements-dev.txt`, `orbit-wizard-blue.spec`, `packaging/`, `.github/workflows/build.yml`.

### Out of Scope — Other roadmap candidates
- No Linux CI job, `MainWindow` split, or `gui_validation.py` move.

### Out of Scope — Historical records
- `.moai/reports/plan-audit/PROJECT-review-1.md` and `.moai/project/codemaps/data-flow.md:29` are not edited.
