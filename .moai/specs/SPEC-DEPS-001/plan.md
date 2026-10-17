# SPEC-DEPS-001 — Implementation Plan (Tier S)

## §A Context

Remove the unused `requests` runtime dependency, the four pins it exclusively requires, and its license row. The change touches three manifest/notice files and no Python source. Evidence is in `spec.md` §1.

## §B Known Issues / Evidence Base

- No `import requests` / `from requests` in `src/`, `tests/`, `tools/`, `packaging/`, `orbit-wizard-blue.spec`, `.github/`. HTTP is `urllib.request` (`src/orbit_wizard_blue/data.py:15-17`).
- `pip show` (primary `.venv`): requests is Required-by orbit-wizard-blue only; urllib3 2.8.0, certifi 2026.7.22, idna 3.20, charset-normalizer 3.5.2 are each Required-by requests only. `pip check` is clean.
- CI installs `requirements-dev.txt` (which has `-r requirements.txt` at line 1) and then `pip install --no-deps -e .` (`.github/workflows/build.yml:22,24`). CI resolves `requirements.txt`, not the pyproject dependency list.
- PyInstaller collects only imported modules plus the explicit `copy_metadata` list (`orbit-wizard-blue.spec:10`: orbit-wizard-blue, sgp4, numpy, scipy, astropy, pyerfa). requests is neither imported nor listed, so the frozen bundle is not expected to contain it today.

## §C Pre-flight

1. Confirm the branch is current against `origin/main` (Pre-Spawn Sync Check).
2. **Record `base_sha`.** Before the first run-phase edit, run `git rev-parse HEAD` and record the output in `progress.md` §E.2 as `base_sha: <sha>`. Every commit-range check in `spec.md` §3 uses this value as `<base_sha>`. Do not substitute a merge base with `main`: the SPEC lives on branch `WT-project-docs`, and under a main-direct route the merge base would be HEAD itself.
3. Set `$PY312` to the primary checkout's `.venv/bin/python3.12` (bare `python` is not on PATH on the reference host; `/usr/bin/python3` is 3.10 and has no `tomllib`).
4. Record the baseline in the existing primary `.venv`: `"$PY312" -m ruff check src tests tools`, `QT_QPA_PLATFORM=offscreen ORBIT_WIZARD_DISABLE_3D=1 "$PY312" -m pytest -q` (record the pass count), `QT_QPA_PLATFORM=offscreen "$PY312" -m orbit_wizard_blue --smoke-test`.
5. Re-run `git grep -n -E '^\s*(import|from)\s+(requests|urllib3|certifi|idna|charset_normalizer)\b' -- src tests tools packaging orbit-wizard-blue.spec .github` and confirm it is empty before deleting anything.

## §D Constraints

- Manifest-only change. No edits under `src/`, `tests/`, `tools/`, `packaging/`, `.github/`, nor to `orbit-wizard-blue.spec` or `requirements-dev.txt`.
- Deletions only; no reordering or reformatting of the remaining lines.
- `development_mode: tdd`: no behavior is added, so there is no RED test to write. Verification-first applies instead: the AC commands in `spec.md` §3 are the executable checks, compared against the §C baseline. Adding a new test file is out of scope.

## §E Self-Verification

Run every AC in `spec.md` §3 (AC-DEPS-001 to AC-DEPS-007) in the §F order and record each command with its verbatim output in `progress.md` §E.2, next to the recorded `base_sha`. Content checks run before the commit; commit-range checks (`<base_sha>..HEAD`) run after it. AC-DEPS-007 is a Gap while the CI run is incomplete or when no run exists for the head commit.

## §F Tasks (ordered by decision-reversibility — most likely to change first)

1. **Confirm the transitive removal set (decision point).** In the primary `.venv`, run `"$PY312" -m pip show urllib3 certifi idna charset-normalizer | grep -E '^(Name|Required-by)'`. Every `Required-by` line must read `requests`; if any other distribution appears, keep that pin and return a blocker report. certifi is also an optional runtime import of astropy (Risk R1); that does not block removal.
2. **Edit `requirements.txt`.** Delete lines 4, 5, 6, 17, 22 (certifi, charset-normalizer, idna, requests, urllib3).
3. **Edit `pyproject.toml`.** Delete line 21 (`"requests==2.32.5",`).
4. **Edit `LICENSES.txt`.** Delete line 12 (the Requests row).
5. **Content checks (no commit needed).** Run AC-DEPS-001 bullets 1-2 (count and full nine-entry list), AC-DEPS-002 bullets 1-3 (no removed pin, 16 pins, header line), AC-DEPS-003 bullet 1 (no Requests row), and AC-DEPS-006 bullet 2 (no `import requests`).
6. **Fresh-environment ACs.** Build `$SCRATCH/venv` outside the repository per AC-DEPS-004, then run AC-DEPS-004 and AC-DEPS-005.
7. **Commit.** One run-phase commit naming SPEC-DEPS-001, staged by explicit pathspec (`git add pyproject.toml requirements.txt LICENSES.txt`).
8. **Commit-range checks (after task 7).** Against the `base_sha` recorded in §C step 2, run the "after the run-phase commit" bullets: AC-DEPS-001 (`git diff --numstat <base_sha>..HEAD -- pyproject.toml` → `0	1	pyproject.toml`), AC-DEPS-002 (no added lines; `0	5	requirements.txt`), AC-DEPS-003 (`0	1	LICENSES.txt`), and AC-DEPS-006 bullet 1 (exactly the three files outside `.moai`).
9. **CI (if pushed).** AC-DEPS-007. If the run is still in progress, wait for it to complete and report its final conclusion; report a Gap if no run exists for the head commit.
10. **Sync-phase doc follow-up (manager-docs).** Delete the rows listed below. Do not edit `.moai/project/codemaps/data-flow.md:29` (verb usage) or `.moai/reports/plan-audit/PROJECT-review-1.md` (historical record).

### Files to modify

Run phase (manager-develop):

| File | Line | Change |
|---|---|---|
| `pyproject.toml` | 21 | delete `  "requests==2.32.5",` |
| `requirements.txt` | 4 | delete `certifi==2026.7.22` |
| `requirements.txt` | 5 | delete `charset-normalizer==3.5.2` |
| `requirements.txt` | 6 | delete `idna==3.20` |
| `requirements.txt` | 17 | delete `requests==2.32.5` |
| `requirements.txt` | 22 | delete `urllib3==2.8.0` |
| `LICENSES.txt` | 12 | delete `Requests: Apache-2.0, https://requests.readthedocs.io/` |

Sync phase (manager-docs):

| File | Line | Change |
|---|---|---|
| `.moai/project/tech.md` | 18 | delete the `requests` row from the dependency table |
| `.moai/project/tech.md` | 68 | delete the "`requests` declared but unused" Known Risks row |
| `.moai/project/product.md` | 46 | delete the "Remove the unused `requests` dependency" roadmap bullet |
| `.moai/project/codemaps/dependencies.md` | 16 | delete the `\| requests \| none (declared only) \|` row |

## Risks

| ID | Risk | Evidence / Mitigation |
|---|---|---|
| R1 | certifi is an optional runtime import of astropy: `astropy/utils/data.py:1200-1203` uses `certifi.where()` as the CA bundle for `download_file` when certifi is installed. | The app does not reach that path: `data.py:161,164-165,274` disable astropy auto-download and the leap-second auto URLs, and IERS/leap-second files are fetched through the app's own `urllib.request.urlopen` (`data.py:156,409`) and opened as local paths (`data.py:276-277`, `cache=False`). CelesTrak downloads already use the default SSL context. Residual: future code calling astropy `download_file` would fall back to the system CA store. AC-DEPS-005 and the CI frozen smoke test cover current paths. |
| R2 | A fresh environment rebuilt from `requirements.txt` could be broken (another package needs a removed pin, or pip resolves one anyway). | AC-DEPS-004 (`pip check`, `pip show`, `find_spec`) runs in a fresh scratch venv, not the existing `.venv`; AC-DEPS-005 then runs the smoke test, ruff, and pytest there. |
| R3 | Stale editable-install metadata: in a reused venv, uninstalling requests without re-running `pip install --no-deps -e .` makes `pip check` report `orbit-wizard-blue 0.1.0 requires requests`. | Re-run `pip install --no-deps -e .` after the edit in any reused venv. The fresh-venv ACs avoid this by construction. Existing dev venvs may keep the now-unused packages harmlessly. |
| R4 | The fresh venv needs network access to PyPI (PySide6 and others are large). | If offline, report AC-DEPS-004/005 as Gaps and rely on the reused primary `.venv` (after the R3 reinstall) plus CI. Do not claim PASS. |
| R5 | The CI install is Windows-only; Linux results do not prove the Windows frozen build. | AC-DEPS-007 (REQ-DEPS-006); a Gap while the run is incomplete or if no run exists. |
| R6 | `python3.12` is not on PATH on the reference host. | Use the primary checkout's `.venv/bin/python3.12` as `$PY312`. |

## §G Anti-Patterns

- Do not delete the other `requirements.txt` pins (`packaging`, `PyYAML`, `typing_extensions`, `pyerfa`); astropy and other packages need them.
- Do not treat `requests` identifiers in the tests as library imports.
- Do not `git add -A`; stage the three files by pathspec.
- Do not report AC-DEPS-004/005/007 as PASS without a fresh run of those exact commands.

## MX Tag Plan

None. No Python source file is modified, so there is no function to annotate. Sync-phase MX validation should confirm zero tag changes.

## §H Cross-References

- `.moai/project/tech.md` (dependency table, Known Risks), `.moai/project/product.md` (Roadmap Candidates), `.moai/project/codemaps/dependencies.md`
- `.github/workflows/build.yml:22,24`, `orbit-wizard-blue.spec:10`, `src/orbit_wizard_blue/data.py:15-17,156,161-165,274-277,409`
