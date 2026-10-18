# SPEC-GITOWN-001 — Progress

## §E.1 Plan-phase Audit-Ready Signal

Plan-phase notes (authoring session 2026-10-18, iteration 1):
- The conflict inventory in `spec.md` §1 was read from `AGENTS.md`, the five agent definitions, seven workflow files, `spec-workflow.md`, `CLAUDE.md`, and `git-strategy.yaml`.
- Not verified: how `moai update` treats edited files; what consumes the `git-strategy.yaml` automation keys.

Iteration 2 (2026-10-18), addressing the plan-audit report `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18.md`:
- X-1: all clarification markers removed from plan.md. Answered by user decisions: coordinator identity (the coordinator = the MoAI orchestrator), future of `manager-git` (kept, proposal-only), Frozen zone (not edited; override rule), tracking scope (the 14 files). Measurements moved to plan §C with ACs: `moai update` (AC-GITOWN-013), rule loading (AC-GITOWN-011). Deferred: `git-strategy.yaml`, technical guard, roster note. The one remaining decision (removing `Bash`/`bypassPermissions` from `manager-git`, REQ-GITOWN-005) was decided by the user on 2026-10-18; no open decisions remain.
- X-2: single tracking scope in REQ-GITOWN-007; the "plus any file added" clause is deleted from AC-GITOWN-012.
- X-4: AC-GITOWN-013 always performs the real scratch update with an isolated `HOME` and decides from `cmp`.
- X-5: Conventions mark ACs `[coordinator-run]` and state the coordinator runs all commands.
- X-7: `related_specs` removed. X-8: the update-record REQ became a measurement AC. X-9: second-hand provenance reworded.
- G-1: `tier: M`, acceptance.md added, REQ/AC counts within the Tier M ceilings (7 REQ, 13 AC), threshold 0.80. G-2: `spec-workflow.md` is not edited; REQ-GITOWN-003 adds `.claude/rules/project/git-ownership.md`; REQ-002 and the tracking set were adjusted (13 edited + 1 new = 14 files); AC-GITOWN-006 proves the Frozen file is untouched. G-3: inventory completed (`manager-git.md:96,119-120,127,160-162`; `manager-develop.md:81`; `sync/delivery.md:213-330`; `plan/spec-assembly.md:281,312-314`; extra hits from the regex re-scan: `run.md:51,152`, `plan.md:97`, `sync.md:52,126`, `sync/delivery.md:46,448`, `manager-develop.md:234`); AC-GITOWN-002 and -004 (Scan S) fail while imperative Git text remains. G-4: AC-GITOWN-010 (carve-out grep) and AC-GITOWN-011 (probe includes "run git status"). G-5: persona sentence now uses "orchestrator". G-6: AC-GITOWN-011 uses three trials in a scratch repo with no remote and no `gh` authentication. G-7: the "inside the Frozen paragraph" wording is removed; the SPEC no longer edits those lines. G-8: confirmed accurate by the audit.
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

Run session 2026-10-18. base_sha: 6d87042e086624256ed751a32dee61552fabc580. Run commit: cbdf400 (14 paths staged by pathspec; the pre-commit gate's pytest aborts in Qt without a display, so the commit ran with `QT_QPA_PLATFORM=offscreen`; the hook was not bypassed). Mode: serial, two manager-develop spawns (agents + rule; workflows + CLAUDE.md), both in isolated worktrees because the targets are untracked in the primary checkout; the coordinator copied the results back and ran every check below. No sub-agent ran git or gh.

- RED baseline (Scan S, before edits, this tree): agents 29 hits (manager-git.md 27, manager-develop.md 1, manager-docs.md 1); workflows 31 hits (delivery.md 22, spec-assembly.md 6, run.md 2, plan.md 1). Saved in the session scratchpad (red_a5.txt, red_w8.txt).
- AC-GITOWN-001: PASS. `grep -L -F 'proposed repository action'` over A5 printed nothing; removal greps printed 0 for all listed strings; `grep -c -i -E 'proposal-only|proposes? '` on manager-git.md printed 11.
- AC-GITOWN-002: PASS. Scan S over A5 printed nothing (29 hits before).
- AC-GITOWN-003: PASS. `grep -L` over W8 printed nothing; every listed `grep -c -F -e` printed 0.
- AC-GITOWN-004: PASS. Scan S over W8 printed nothing (31 hits before).
- AC-GITOWN-005: PASS. exit=0; `^paths:` count 0; the four phrases >= 1 (1, 4, 1, 2); proposal-only 1; 24 lines; Route A 3, Route B 2.
- AC-GITOWN-006: PASS. `sha256sum -c` over the 148 recorded files (rules/moai, hooks, config sections, moai binary): 148 OK, 0 not OK.
- AC-GITOWN-007: PASS. `grep -L -F` for the prohibition sentence over A5 printed nothing.
- AC-GITOWN-008: PASS. frontmatter `grep -c -E 'Bash|bypassPermissions'` printed 0.
- AC-GITOWN-009: PASS. `git diff --quiet 6d87042..HEAD -- AGENTS.md` exit=0.
  - Amended after the run (user decision: the Astra name is a leftover of earlier Codex work): AGENTS.md now differs from base_sha by the name replacement only. Re-run of the amended AC-GITOWN-009 and -012: `grep -c -F Astra AGENTS.md` = 0; ownership-sentence grep = 1; `git diff --numstat <base_sha> -- AGENTS.md` = `3<TAB>3<TAB>AGENTS.md`; name-only diff excluding .moai/specs and AGENTS.md = 14 paths.
- AC-GITOWN-010: PASS. carve-out grep over A5, W8 and the rule file: exit=1, no match.
- AC-GITOWN-011: GAP. No live Claude Code probe session (three manager-git trials plus a fresh-session rule-loading probe) was run in this session; reported as a Gap, not a pass.
- AC-GITOWN-012: PASS. `git ls-files --error-unmatch` on the 14 paths: 14, exit 0; `git status --porcelain --` on them: empty; `git diff --name-only 6d87042..HEAD -- . ':(exclude).moai/specs'`: exactly the 14 paths.
- AC-GITOWN-013: MEASURED (negative result, Gap). Scratch copy with isolated HOME. Plain `moai update --templates-only --no-hooks --yes` printed "Up to date, Skipping sync": all 14 files preserved, 0 files created. With `--force`: 13 managed files overwritten-or-merged (the 5 agents, the 7 workflow files, CLAUDE.md); `.claude/rules/project/git-ownership.md` preserved; no user-level state created in the isolated HOME. So the edits survive a normal update only while the version matches; a forced update, or a version bump that re-deploys templates, restores the old text. Restoring step: re-apply commit cbdf400 (`git show cbdf400 -- <path>` then checkout of the paths). The override rule outside the moai/ namespace persists.

Residual: wording that sounds like Git work but names no executor remains (delivery.md frontmatter/heading "Git Operations and Delivery", trigger lists naming manager-git). The Stop-hook review gate also flagged out-of-scope findings in `.claude/hooks/moai/handle-codex-review-gate.sh` and `.claude/skills/moai-workflow-project/scripts/navigator-audit.sh` and `handle-session-start-navigator.sh`; not touched (REQ-GITOWN-007).

## §E.3 Run-phase Audit-Ready Signal

run_status: audit-ready (AC-001..010 and -012 pass; AC-011 Gap; AC-013 measured, negative)
run_commit_sha: cbdf400
run_complete_at: 2026-10-18

## §E.4 Sync-phase Audit-Ready Signal

sync_complete_at: 2026-10-18
sync_status: audit-ready
sync_commit_sha: d30b015
sync_branch: worktree-sync-gitown (not yet merged to main)

F1 re-check after the sync commit (HEAD d30b015, this tree): `git diff --numstat 6d87042 -- AGENTS.md` printed `3<TAB>3<TAB>AGENTS.md` (AC-009 PASS); `git status --porcelain --` over the 5 agent files, the rule file and AGENTS.md printed nothing (AC-012 clean-tree condition PASS); `git diff --name-only 6d87042 HEAD -- . ':(exclude).moai/specs'` printed 15 paths = the 14 SPEC paths plus AGENTS.md (the post-run user amendment).

Verification (run by the orchestrator in the sync session; tree = HEAD fb4cbd9 plus the uncommitted "(Astra)" removal):

- Claim: test suite passes. Command: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q --no-header -p no:cacheprovider`. Output: `169 passed, 4 warnings in 12.69s`, exit=0. Evidence: `.moai/state/verify/sync-gitown/pytest.txt`.
- Claim: lint is clean. Command: `.venv/bin/python -m ruff check .`. Output: `All checks passed!`, exit=0. Evidence: `.moai/state/verify/sync-gitown/ruff.txt`.
- Snapshot: `moai verify check --key-current` exit=1, "no snapshot recorded for the current working-tree key"; no snapshot was consumed, both commands above were re-executed.
- Files outside `.md` changed: none. `CHANGELOG.md` does not exist and `README.md` has no Git-ownership content, so neither is edited.

AC status (from §E.2): AC-GITOWN-001..010 and -012 PASS; AC-GITOWN-011 Gap (no live Claude Code probe session); AC-GITOWN-013 measured, negative (edits survive a plain `moai update` only while the version matches; a forced update restores the old text in 13 managed files).

Sync-audit (sync-auditor, opus): verdict PASS-with-debt, weighted score about 80.6, harmonic mean about 80, must-pass dimensions Functionality and Security above threshold. It re-ran the Scan S, carve-out, frontmatter and rule-file checks (AC-001..005, 007, 008, 010 PASS), pytest `169 passed` and ruff clean. It ran no git or gh (project rule). Findings: F1 (blocking, resolved by this commit) the "(Astra)" removal was uncommitted, so AC-012 could not hold; F2 AC-006 `protected_sha256` record was not preserved; F3 `manager-git.md` and `delivery.md` proposed actions include `git checkout main`, `git reset --hard`, `git switch -c`, which the orchestrator must run in a worktree under `main-checkout-branch-guard.md`; F4 `acceptance.md` line 3 still names spec.md v0.2.0 (manager-spec owns it); F6 `manager-git.md` hard-codes `--squash` and mixes a slash command into a bash block; F7 "worktree-isolated branches" wording in `manager-lead.md` overlaps AGENTS.md "worktrees". F2-F4, F6 and F7 are optional follow-ups. Cross-model audit (`audit_multi`) was not run because its backends read uncommitted changes through git.
Evidence files live in the primary checkout at `/home/rico/Desktop/Project/orbit-wizard-blue/.moai/state/verify/sync-gitown/` (pytest.txt, ruff.txt).

Gaps:

- AC-GITOWN-006 `protected_sha256` hash record was not preserved; only mtime evidence (no protected file changed after 2026-10-18 11:00) supports it, so it is a Gap, not a pass.
- AC-GITOWN-011 behavioral probe (three manager-git trials and fresh-session rule loading) was not observed.
- No verification snapshot existed to attribute against; the evidence above is this session's re-execution only.
- `sync_commit_sha` is unknown until the sync commit lands; the orchestrator backfills it.

Residual-risk:

- A forced `moai update`, or a version bump that re-deploys templates, restores the pre-SPEC text in the 5 agents, 7 workflow files and CLAUDE.md; recovery is re-applying commit cbdf400. The project rule `.claude/rules/project/git-ownership.md` persists.
- Rule adherence by live agents is untested (AC-GITOWN-011), so an agent could still attempt `git` or `gh`.
- Executor-neutral Git wording remains in `delivery.md` and the `manager-git` trigger lists.
- The Stop-hook review gate reported three out-of-scope defects in untracked Navigator utilities (`navigator-audit.sh` feature-table parsing and stale-override matching, `handle-session-start-navigator.sh` backslash escaping); they are untouched per REQ-GITOWN-007 and need a separate task.
