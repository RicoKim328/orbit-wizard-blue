# SPEC-HOOKS-001 — Progress

## §E.1 Plan-phase Audit-Ready Signal

Plan-phase notes (authoring session 2026-10-18, iteration 1):
- Defect evidence is read from the primary checkout; reproduction status is stated per defect in `spec.md` §1 (D1 partial, D2 yes, D3 mechanism only, D4 no, D5 partial).
- Not verified by the author: real `handle-stop-goal.sh` end-to-end, `navigator-regen.sh` end-to-end, Stop block enforcement on Claude Code 2.1.302, `moai update` behavior, full Stop-hook path of the D5 patch, contents of upstream issue #1827 beyond a WebFetch summary.

Iteration 2 (2026-10-18), addressing the plan-audit report `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18.md`:
- X-1: all clarification markers removed from plan.md. Answered by user decisions: tracking scope (exactly the four files), status-line path ownership (REQ-HOOKS-003). Moved to measurement tasks with ACs: `moai update` treatment (AC-HOOKS-007), schema enforcement on 2.1.302 (AC-HOOKS-008). Decided: wrapper contract is dispatch once then exit 0 (REQ-HOOKS-001); evaluator exit-code question dropped.
- X-2: single tracking scope in REQ-HOOKS-007; the "plus any file added" clauses are deleted from AC-HOOKS-006.
- X-3: the user-specific path in `.moai/status_line.sh:29-31` is owned here (REQ-HOOKS-003, AC-HOOKS-002).
- X-4: AC-HOOKS-007 always performs the real scratch update and decides from `cmp`, with an isolated `HOME`.
- X-5: Conventions mark ACs `[coordinator-run]` and state the coordinator runs all section-3 commands.
- X-7: `related_specs` removed from the frontmatter. X-8: the update-record REQ became a measurement AC. X-9: second-hand provenance reworded as relayed by the coordinator.
- H-1: REQ-HOOKS-005/AC-HOOKS-004 pin the top-level form; AC-HOOKS-008 is the 2.1.302 live check. H-2: REQ-HOOKS-001 states exit 0. H-3: REQ-HOOKS-006 and AC-HOOKS-005 select existing directories; the application-lint bullet is removed. H-4: `export SCRATCH` in Conventions. H-5: plan task 1 edits only `:377-383` and `:387`; D4 cites `:15` and `:35`. H-6: the byte-identical clause is dropped. H-7: RED baseline in plan §C step 2. H-8: Out-of-Scope bullet for `navigator-audit.sh`. H-9: plan risk R2. H-10: gate commands run under `env -u`. H-11: heading corrected in spec-compact.md. Minor: D3 "Derived by reading"; backup copied into evidence (C3).
- Deferred with reason: gate-log visibility of skipped checks (needs no decision to start; follow-up SPEC).

Iteration 3 (2026-10-18), addressing `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18-iter2.md`:
- H2-1 (minor, false failure): fixed. AC-HOOKS-004 writes the advisory re-run as `env -u MOAI_SYNC_GATE_BLOCKING -u MOAI_AUTONOMY_TIER MOAI_SYNC_GATE_BLOCKING=0 CLAUDE_PROJECT_DIR=... bash ...` (assignment after the `-u` options); the convention is stated in Conventions.
- H2-2 and C-1: fixed. `protected_sha256:` (every other hook and the `moai` binary) is recorded at the first run edit and checked with `sha256sum -c` in AC-HOOKS-006, so REQ-HOOKS-008 has a check that can fail.
- H2-3 (minor): fixed. Plan task 5 also removes the stale comment at `status_line.sh:26-28`. H2-4: accepted as stated (AC-HOOKS-007/-008 are measurements). C-2: fixed (contiguous `base_sha`, one run phase at a time, order HOOKS, ENV, GITOWN, REVGATE). C-3: fixed (scratch copy built with `tar` excluding `.git`/`.venv`; created/changed file list recorded).
- `plan_status` stays audit-ready: no blocker or major finding was open for this SPEC.

plan_status: audit-ready
plan_complete_at: 2026-10-18

## §E.2 Run-phase Evidence

_<pending run-phase>_

## §E.3 Run-phase Audit-Ready Signal

_<pending run-phase>_

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase>_
