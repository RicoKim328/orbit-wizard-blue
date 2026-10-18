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

_<pending run-phase>_

## §E.3 Run-phase Audit-Ready Signal

_<pending run-phase>_

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase>_
