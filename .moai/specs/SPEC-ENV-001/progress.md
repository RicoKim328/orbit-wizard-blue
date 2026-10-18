# SPEC-ENV-001 — Progress

## §E.1 Plan-phase Audit-Ready Signal

Plan-phase notes (authoring session 2026-10-18, iteration 1):
- The `env` block and PATH line are quoted exactly in `spec.md` §1 E1 (`.claude/settings.json:349-356`). The effective PATH in the authoring session equals that literal.
- Reproduction status: effective PATH observed (partial); replace-versus-merge semantics, other developers' consequences, and the origin of the entry were not reproduced or verified.

Iteration 2 (2026-10-18), addressing the plan-audit report `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18.md`:
- X-1: all clarification markers removed from plan.md. Origin of the PATH entry, replace-versus-merge, `$PATH` expansion and `moai update` preservation became measurement tasks (plan §C steps 2-5) with ACs (AC-ENV-004, AC-ENV-008); the launching-shell question became the AC-ENV-002 precondition; the status-line path was answered by the user decisions (owned by SPEC-HOOKS-001).
- X-2: single tracking scope (exactly `.claude/settings.json` and `.gitignore`) in REQ-ENV-005; the "plus any file added" clause is deleted from AC-ENV-007.
- X-3: ENV only references `.moai/status_line.sh:29-31`; owned by SPEC-HOOKS-001 (REQ-HOOKS-003).
- X-4: AC-ENV-008 always performs the real scratch update with an isolated `HOME` and decides from `cmp`.
- X-5: Conventions mark ACs `[coordinator-run]` and state the coordinator runs all section-3 commands.
- X-7: `related_specs` removed. X-8: the update-record REQ became a measurement AC. X-9: reported consequences are worded as relayed by the coordinator.
- E-1: REQ-ENV-002 keeps the hook half and AC-ENV-005 adds a hook-process probe; the Bash-tool probe is AC-ENV-004. E-2: REQ-ENV-001 is conditional on `moai` resolving through the launching shell's PATH (AC-ENV-002 precondition); E4 and R1 extended to all three wrappers; R2 notes that the Codex plugin's `node` hooks start running once the override is gone. E-3: REQ-ENV-003 restated as a property of the repository's `.gitignore`. Baseline measurement of replace-versus-merge in plan §C step 3.
- Deferred with reason: adding a `$HOME/.local/bin` tier to the three wrappers (unnecessary while the precondition holds).

Iteration 3 (2026-10-18), addressing `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18-iter2.md`:
- E2-1 (major): fixed. AC-ENV-002 expects `N` at least 1 per wrapper (real counts read: 2, 2, 1).
- E2-2 (major): fixed. `$LAUNCH_PATH` is supplied by the user from an interactive terminal (the coordinator session is daemon-spawned and cannot observe it), recorded with provenance `user-supplied`; if absent, AC-ENV-002/-004/-005 are Gaps. AC-ENV-004/-005 launch with an explicit `env PATH="$REPO/.venv/bin:$LAUNCH_PATH"`; the baseline run under the original `settings.json` discriminates replace (first entry `/home/rico/.local/bin`) from merge (first entry the venv).
- E2-3 (minor): fixed. The hook-probe fixture creates `$SCRATCH/hookprobe/.claude`. E2-4: accepted as Gap-eligible; AC-ENV-005 is named the deterministic evidence. E2-5 and C-1: fixed (`sha256sum -c` on the recorded hook and `settings.local.json` hashes replaces `git diff -- .claude/hooks`). C-2: fixed (contiguous `base_sha`, one run phase at a time, order HOOKS, ENV, GITOWN, REVGATE). C-3: fixed (scratch copy built with `tar` excluding `.git`/`.venv`, file list before and after).
- `plan_status` stays audit-ready: the two major findings are fixed.

plan_status: audit-ready
plan_complete_at: 2026-10-18

## §E.2 Run-phase Evidence

Run date 2026-10-18. `base_sha: b28cbe1449664ee1a0a99668679b0bb14a4344b6`. Pre-change copy: `$SCRATCH/settings.before.json` (`$SCRATCH` = the job scratch directory, outside any repository). Coordinator-run.

`$LAUNCH_PATH` (provenance: user-supplied, from an interactive terminal):
`/home/rico/go/bin:/home/rico/.local/bin:/home/rico/.local/bin:/home/rico/.nvm/versions/node/v24.19.0/bin:/home/rico/.local/bin:/home/rico/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin`

- AC-ENV-002 PASS: `PATH="$LAUNCH_PATH" command -v moai` printed `/home/rico/.local/bin/moai`; `grep -c -F 'command -v moai'` printed `chain-event.sh:1`, `handle-multi-review-gate.sh:2`, `handle-codex-review-gate.sh:2`.
- AC-ENV-001 PASS. RED first (original file): `True` / `False`. After the edit: `False` / `True`; `diff settings.before.json settings.json | grep -c '^[<>]'` printed `3`.
- AC-ENV-003 PASS. RED first: line 355 matched, `exit=0`. After: `exit=1`.
- AC-ENV-006 PASS. RED first: `git -c core.excludesFile=/dev/null check-ignore -q .claude/settings.local.json` gave `exit=1`; after adding one line to `.gitignore` (commit `71249a1`) it gave `exit=0`; the diff holds one added line and no removed line.
- Replace versus merge: **replace**. Baseline hook probe (original `env` block, launched with `env PATH="$REPO/.venv/bin:$LAUNCH_PATH"`) wrote a PATH whose first entry is `/home/rico/.local/bin`, the override literal.
- AC-ENV-005 **FAIL on this machine, root cause outside this SPEC's files**: after the change the hook still saw `/home/rico/.local/bin:/home/rico/go/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin` as its PATH. The user-level file `~/.claude/settings.json:18` carries the same `"PATH"` literal and overrides the inherited PATH for every project. The project-level change is correct and necessary but not sufficient here. Removing the user-level entry is outside this SPEC's scope (shared repository files only) and needs the user's decision.
- AC-ENV-004 Gap: a `claude -p` probe inside the project was taken over by the Stop review gate (it tried unrelated review fixes and printed no PATH lines). Not reported as a pass. The deterministic hook probe above stands in for it; it is subject to the same user-level override.
- AC-ENV-008 Gap: this session cannot redirect `HOME` (the sandbox refuses a `HOME=` prefix), and running `moai update` against the real home was judged unsafe. The scratch copy was built (160 files); no update was run. To measure: `cd <scratch copy> && HOME=<empty dir> moai update --templates-only --no-hooks --yes`, then `cmp` the settings file and check `'PATH' in env`.
- Protected-file record: `sha256sum` of 43 hook scripts plus `.claude/settings.local.json` (44 lines); `sha256sum -c` reported 44 `OK`. Their mtimes (2026-10-17) precede this run, so they were not modified. The record was taken after the settings edit rather than before it, but none of these files was edited in this run.
- Observed side effect (R2): the baseline session's SessionEnd hook of the Codex plugin failed with `SyntaxError: Unexpected token '?'` because the override puts Node v12 first.
- Quality-gate note: the commit hook runs `pytest` without `QT_QPA_PLATFORM=offscreen`, so the GUI tests abort; with the variables set, `169 passed`. The hook configuration is outside this SPEC.

## §E.3 Run-phase Audit-Ready Signal

run_status: partial. AC-ENV-001, -002, -003, -006 pass; AC-ENV-007 is checked after the commit. AC-ENV-005 fails because of a user-level `PATH` override in `~/.claude/settings.json:18`; AC-ENV-004 and -008 are Gaps.

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase>_
