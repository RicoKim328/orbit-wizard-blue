# SPEC-HOOKS-001 (compact)

Auto-generated summary of `spec.md` v0.3.0 and `plan.md`: requirements, acceptance criteria, files to modify, exclusions. `spec.md` is authoritative.

`$REPO` = checkout holding the hardened files; `export SCRATCH` = fresh dir outside any git repo; `<base_sha>` = `git rev-parse HEAD` taken immediately before this SPEC's first run edit (run phases one at a time: HOOKS, ENV, GITOWN, REVGATE); `protected_sha256:` (other hooks, the `moai` binary) recorded there and checked with `sha256sum -c`. The coordinator runs every command in `spec.md` §3; ACs marked [coordinator-run] call git (directly or via a script), run `moai`, or open live sessions.

## Defects (reproduction status as stated in spec.md; the defects were relayed by the coordinator from the Codex review gate)

- **D1** `handle-stop-goal.sh:64-66,69-71,74-76`: `exec` in a pipeline falls through tiers (partial: isolated replica only).
- **D2** `.moai/status_line.sh:23,30,35,40`: `exec` skips the EXIT trap, leaking a temp file (yes, real file); `:29-31` hard-codes a user path.
- **D3** `navigator-regen.sh:251`: tab-IFS `read` collapses empty fields (mechanism only).
- **D4** `sync-phase-quality-gate.sh:391-399`: block decision nested in `hookSpecificOutput` (not reproduced; documentation says top-level).
- **D5** `sync-phase-quality-gate.sh:228-241`: ruff skipped when only in `.venv` (partial; patched locally, untracked).

## Requirements

- **REQ-HOOKS-001**: On a Stop event with an armed goal the wrapper shall invoke `moai hook stop-goal` exactly once (first resolving tier) and then exit 0; goal-less sessions exit 0 without invoking `moai`.
- **REQ-HOOKS-002**: The status-line wrapper shall run the resolved `moai` without `exec` in every branch and exit with its status so the trap removes the temp file.
- **REQ-HOOKS-003**: The status-line wrapper shall contain no absolute user-home path and resolve `moai` only via `PATH` and `$HOME`-relative locations.
- **REQ-HOOKS-004**: The navigator script shall render each `progress-map.md` column from its own field when `phase`/`module` is omitted.
- **REQ-HOOKS-005**: In blocking mode the gate shall emit one JSON object with top-level `decision:"block"`, non-empty `reason`, and `systemMessage`, no nested `decision`, exit 0; no `decision` key anywhere in advisory mode or on pass.
- **REQ-HOOKS-006**: For Python projects the gate shall run the venv ruff (else PATH ruff) with `check` plus only the existing directories among `src`, `tests`, `tools`, or `check .` when none exists.
- **REQ-HOOKS-007**: Exactly the four hardened files shall be tracked in git.
- **REQ-HOOKS-008**: No other tracked file, hook, the `moai` binary, or `AGENTS.md` shall change.

## Acceptance Criteria

| AC | Check | Pass condition |
|---|---|---|
| AC-HOOKS-001 | stub `moai` at 3 tiers; run `handle-stop-goal.sh` with armed goal | `exit=0`, 1 stdout line, 1 call; per-tier fallbacks give 1 call; no goal or no binary gives `exit=0`, no call/empty stdout |
| AC-HOOKS-002 | static greps on `.moai/status_line.sh` for `exec` and home paths; run with stub (PATH, `$HOME/go/bin`, `$HOME/.local/bin` tiers) and scratch `TMPDIR` | both greps `exit=1`; stub line printed, `exit=7`, 0 files left in each case |
| AC-HOOKS-003 | `navigator-regen.sh` on three fixture SPECs; exact-row `grep -c -F -x` | each expected `progress-map.md` row count `1`; `capability-map.md` guard row `1` |
| AC-HOOKS-004 | gate in scratch repo with failing ruff stub as `env -u ... [VAR=value] CLAUDE_PROJECT_DIR=... bash`; `python3` JSON check; grep for the nested form | `exit=0`, 1 line, `True`; no nested emission; advisory (assignment after the `-u` options) has no `decision`; pass is empty |
| AC-HOOKS-005 | gate with venv stub: all dirs, missing `tools`, none, PATH fallback, neither | argv `check src tests tools`, `check src tests`, `check .`, `check src tests`; silent `exit=0` |
| AC-HOOKS-006 | `git ls-files --error-unmatch`, `git status --porcelain`, name-only diffs vs `<base_sha>`; `sha256sum -c` of the protected record | four paths tracked and clean; diff lists exactly them; nothing under `src tests tools packaging .github AGENTS.md`; every protected file `OK` |
| AC-HOOKS-007 | real `moai update --templates-only --no-hooks --yes` in a scratch copy with isolated `HOME`; `cmp` per file | verbatim output and `preserved`/`overwritten-or-merged` per file; any difference is a Gap |
| AC-HOOKS-008 | throwaway project with a Stop hook that blocks once; `claude -p` | stop log has 2 entries, second with `stop_hook_active:true`; Gap if no live session |

## Files to Modify

- `.claude/hooks/moai/sync-phase-quality-gate.sh:228-241,377-383,387,391-399`
- `.claude/hooks/moai/handle-stop-goal.sh:64-66,69-71,74-76`
- `.claude/skills/moai-workflow-project/scripts/navigator-regen.sh:251-260`
- `.moai/status_line.sh:23,29-31,35,40`

## Exclusions

### Out of Scope — Application code
- No change under `src/`, `tests/`, `tools/`, `packaging/`, `.github/`, or to `AGENTS.md`.

### Out of Scope — Other hooks and the moai binary
- No change to `handle-pre-tool.sh`, other wrappers, `navigator-audit.sh`, the `moai` binary, or hook registration in `.claude/settings.json`.

### Out of Scope — Environment, ownership, and review-gate issues
- PATH override is SPEC-ENV-001; Git ownership is SPEC-GITOWN-001; repeated review-gate feedback is SPEC-REVGATE-001.

### Out of Scope — Cleanup and upstream reporting
- No deletion of leaked `/tmp` files; no edit of upstream issue #1827 and no upstream patch.
