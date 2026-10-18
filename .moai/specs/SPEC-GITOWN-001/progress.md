# SPEC-GITOWN-001 — Progress

## §E.1 Plan-phase Audit-Ready Signal

Plan-phase notes (authoring session 2026-10-18, iteration 1):
- The conflict inventory in `spec.md` §1 was read from `AGENTS.md`, the five agent definitions, seven workflow files, `spec-workflow.md`, `CLAUDE.md`, and `git-strategy.yaml`.
- Not verified: how `moai update` treats edited files; what consumes the `git-strategy.yaml` automation keys.

Iteration 2 (2026-10-18), addressing the plan-audit report `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18.md`:
- X-1: all clarification markers removed from plan.md. Answered by user decisions: coordinator identity (Astra = the MoAI orchestrator), future of `manager-git` (kept, proposal-only), Frozen zone (not edited; override rule), tracking scope (the 14 files). Measurements moved to plan §C with ACs: `moai update` (AC-GITOWN-013), rule loading (AC-GITOWN-011). Deferred: `git-strategy.yaml`, technical guard, roster note. The one remaining decision (removing `Bash`/`bypassPermissions` from `manager-git`, REQ-GITOWN-005) was decided by the user on 2026-10-18; no open decisions remain.
- X-2: single tracking scope in REQ-GITOWN-007; the "plus any file added" clause is deleted from AC-GITOWN-012.
- X-4: AC-GITOWN-013 always performs the real scratch update with an isolated `HOME` and decides from `cmp`.
- X-5: Conventions mark ACs `[coordinator-run]` and state the coordinator runs all commands.
- X-7: `related_specs` removed. X-8: the update-record REQ became a measurement AC. X-9: second-hand provenance reworded.
- G-1: `tier: M`, acceptance.md added, REQ/AC counts within the Tier M ceilings (7 REQ, 13 AC), threshold 0.80. G-2: `spec-workflow.md` is not edited; REQ-GITOWN-003 adds `.claude/rules/project/git-ownership.md`; REQ-002 and the tracking set were adjusted (13 edited + 1 new = 14 files); AC-GITOWN-006 proves the Frozen file is untouched. G-3: inventory completed (`manager-git.md:96,119-120,127,160-162`; `manager-develop.md:81`; `sync/delivery.md:213-330`; `plan/spec-assembly.md:281,312-314`; extra hits from the regex re-scan: `run.md:51,152`, `plan.md:97`, `sync.md:52,126`, `sync/delivery.md:46,448`, `manager-develop.md:234`); AC-GITOWN-002 and -004 (Scan S) fail while imperative Git text remains. G-4: AC-GITOWN-010 (carve-out grep) and AC-GITOWN-011 (probe includes "run git status"). G-5: persona sentence now uses "orchestrator (Astra)" per user decision. G-6: AC-GITOWN-011 uses three trials in a scratch repo with no remote and no `gh` authentication. G-7: the "inside the Frozen paragraph" wording is removed; the SPEC no longer edits those lines. G-8: confirmed accurate by the audit.
- `plan_status` stays audit-ready: every finding is addressed or deferred with a reason above.

Iteration 3 (2026-10-18), addressing `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18-iter2.md`:
- G2-1 (major) and C-1: fixed. AC-GITOWN-006, the last bullet of AC-GITOWN-012 and the Definition of Done now use a `protected_sha256:` record taken at the first run edit (all `.claude/rules/moai/` files including `spec-workflow.md`, the hooks, `.moai/config/sections/*.yaml`, the `moai` binary) and `sha256sum -c`; `AGENTS.md`, which is tracked, keeps its `git diff` check.
- G2-2 (minor): fixed. Inventory and plan table add `manager-docs.md:8`, `run.md:165`, `plan/spec-assembly.md:336`; all three files were already in the edited set, so the count stays 14 files (13 edited, 1 new) and 7 REQ / 13 AC (M ceiling 16).
- G2-3 (minor): fixed. Scan S verb list extended (`git -C|show|ls-files|config|clone|init|restore|cherry-pick|remote`, `gh api|run|release|repo|auth`). G2-4 (minor): fixed. The stale progress statement in the iteration-2 entry now says the decision was made. G2-5 (minor): fixed. The rule-layout sentence now says most rules carry frontmatter and always-loaded ones such as `moai-constitution.md` start with an H1. G2-6 (minor): fixed. The override rule is capped at 40 lines and states that other `manager-git` references (`e2e-tester.md:15`, `moai/SKILL.md:122,130,138,224`, `references/reference.md:24`) now mean proposal-only (AC-GITOWN-005).
- C-2: fixed (contiguous `base_sha`, one run phase at a time, order HOOKS, ENV, GITOWN, REVGATE). C-3: fixed (scratch copy built with `tar` excluding `.git`/`.venv`; created/changed file list recorded).
- `plan_status` stays audit-ready: the one major finding is fixed.

plan_status: audit-ready
plan_complete_at: 2026-10-18

## §E.2 Run-phase Evidence

_<pending run-phase>_

## §E.3 Run-phase Audit-Ready Signal

_<pending run-phase>_

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase>_
