# SPEC-ENV-001 (compact)

Auto-generated summary of `spec.md` v0.3.0 and `plan.md`: requirements, acceptance criteria, files to modify, exclusions. `spec.md` is authoritative.

`$REPO` = checkout holding `.claude/settings.json`; `export SCRATCH` = fresh dir outside any git repo; `<base_sha>` = `git rev-parse HEAD` recorded in `progress.md` §E.2; `$SCRATCH/settings.before.json` = pre-change copy; `$LAUNCH_PATH` = the launching shell's PATH, supplied by the user from an interactive terminal (the coordinator session is daemon-spawned and cannot observe it); `base_sha` is taken immediately before this SPEC's first run edit, run phases one at a time (HOOKS, ENV, GITOWN, REVGATE); `protected_sha256:` (hooks, `settings.local.json`) recorded at the first run edit. The coordinator runs every command in `spec.md` §3; ACs marked [coordinator-run] call git, run `moai`, or open live sessions.

## Defect (the Codex-gate report was relayed by the coordinator)

`.claude/settings.json:355` sets `"PATH": "/home/rico/.local/bin:/home/rico/go/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin"` inside the `env` block (`:349-356`). Observed in the authoring session: effective PATH equals that literal; `command -v ruff` fails although `.venv/bin/ruff` exists; `command -v node` is `/usr/bin/node` v12.22.9, on which the Codex plugin script fails with a SyntaxError, while the nvm Node v24.19.0 is not on the PATH. Replace-versus-merge semantics: not proven (measured by AC-ENV-004). Reproduced by author: partial.

## Requirements

- **REQ-ENV-001**: Where `moai` resolves on the launching shell's PATH, the shared `env` block shall not define `PATH` and shall keep its other five entries unchanged.
- **REQ-ENV-002**: When Claude Code starts from a shell with an activated venv `bin` first on PATH, the Bash tool and a hook process shall each see it first, so `ruff` resolves to the venv copy.
- **REQ-ENV-003**: The repository's own `.gitignore` shall exclude `.claude/settings.local.json` without relying on a global ignore file.
- **REQ-ENV-004**: `.claude/settings.json` shall contain no absolute user-home path.
- **REQ-ENV-005**: Exactly `.claude/settings.json` and `.gitignore` shall be tracked for this change, the former with the content satisfying REQ-ENV-001 and -004.
- **REQ-ENV-006**: No other tracked file, hook script, or the `moai` binary shall change.

## Acceptance Criteria

| AC | Check | Pass condition |
|---|---|---|
| AC-ENV-001 | `python3 -c` on `['env']`; `diff` vs `$SCRATCH/settings.before.json \| grep -c '^[<>]'` | `False` then `True`; `3` |
| AC-ENV-002 | `PATH="$LAUNCH_PATH" command -v moai`; `grep -c -F 'command -v moai'` on the three wrappers | a path; `<path>:N` with N at least 1 per wrapper; otherwise blocker report; Gap if `$LAUNCH_PATH` not supplied |
| AC-ENV-003 | `grep -n -E '/(home\|Users)/[^"/ ]+\|[A-Za-z]:\\\\Users' .claude/settings.json` | `exit=1` |
| AC-ENV-004 | baseline then post-change `env PATH="$REPO/.venv/bin:$LAUNCH_PATH" claude -p` printing `printenv PATH \| cut -d: -f1; command -v ruff; command -v node` | baseline first entry discriminates replace/merge; after: `$REPO/.venv/bin`, `$REPO/.venv/bin/ruff`, the `node` that `PATH="$REPO/.venv/bin:$LAUNCH_PATH"` resolves; Gap if no session or no `$LAUNCH_PATH` |
| AC-ENV-005 | `mkdir -p` then throwaway project with the changed `env` block plus a SessionStart hook printing PATH; `env PATH="$REPO/.venv/bin:$LAUNCH_PATH" claude -p` | first PATH entry is `$REPO/.venv/bin`; Gap if no session or no `$LAUNCH_PATH` |
| AC-ENV-006 | `git -c core.excludesFile=/dev/null check-ignore -q .claude/settings.local.json`; `.gitignore` diff added/removed lines | `exit=0`; only additions |
| AC-ENV-007 | `git ls-files --error-unmatch`, `git status --porcelain`, name-only diff vs `<base_sha>`; `sha256sum -c` of the protected record | two paths tracked and clean; diff lists exactly them; every protected file `OK` |
| AC-ENV-008 | real `moai update --templates-only --no-hooks --yes` in a defined scratch copy (`tar`, excluding `.git`/`.venv`) with isolated `HOME`; `cmp`; `PATH` key check; file-list diff | verbatim output; `preserved` or `overwritten-or-merged`; `PATH` present `True/False`; any difference is a Gap |

## Files to Modify

- `.claude/settings.json:354-355` — remove the `PATH` entry and the comma after `NO_FLICKER`
- `.gitignore` — add `.claude/settings.local.json`

## Exclusions

### Out of Scope — Other settings content
- No change to hook registrations, permissions, `statusLine`, model, output style, or the five remaining `env` entries.

### Out of Scope — Other files and the status-line path
- `.moai/status_line.sh:29-31` is owned by SPEC-HOOKS-001; no change to the hook wrappers, `.claude/settings.local.json` content, or shell startup files.

### Out of Scope — Tooling internals
- No change to the `moai` binary or the `moai update` template set.

### Out of Scope — Upstream
- No edit of upstream issue #1827 and no upstream patch.
