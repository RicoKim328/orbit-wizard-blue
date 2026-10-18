# SPEC-GITOWN-001 — Implementation Plan (Tier M)

## §A Context

Rewrite the Git-executing instructions in five MoAI agent definitions, seven workflow files, and `CLAUDE.md` so that sub-agents return a proposed repository action and the orchestrator (Astra, `AGENTS.md:5,13`) executes it; keep `manager-git` as a proposal-only agent with no `Bash` and no `bypassPermissions`; add a project rule that overrides the Frozen Route A/B text in `spec-workflow.md` without editing it. 14 files in all (13 edited, 1 new). Instruction text, one rule file and one frontmatter only; no enforcement mechanism. Direction decided by the user: project-local hardening plus upstream issue https://github.com/modu-ai/moai-adk/issues/1827 (item 5).

User decisions applied in iteration 2: (1) track only the files this SPEC modifies; (2) Astra is the MoAI main session (the orchestrator), and `manager-git` is kept as proposal-only; (3) `spec-workflow.md` is not edited and an override rule is added at `.claude/rules/project/git-ownership.md` (path chosen after reading the rule layout: existing rules live under `.claude/rules/moai/<area>/` with YAML frontmatter and `paths:` globs, and the override is placed outside the `moai/` namespace without `paths:` so it is not path-scoped).

## §B Known Issues / Evidence Base

Read by the author on 2026-10-18:

- `AGENTS.md:1-15` (this worktree); `.claude/agents/moai/manager-git.md:1-30,31-42,90-130,150-175` and regex hits for repository commands in all five agent files; the `tools:`/`permissionMode:` lines of all ten agents (every agent holds `Bash`).
- Workflow lines: `run.md:23,37,51,152,165`, `plan.md:25,37,97`, `sync.md:25,41,52`, `sync/delivery.md:25-60,213-330,446-449`, `plan/spec-assembly.md:268-281,312-314,336,336-342,354-360,383-396`, `run/task-decomposition.md:280-312`, `run/mode-orchestration.md:76-80`.
- Rule and project text: `.claude/rules/moai/workflow/spec-workflow.md:22-64` (`[ZONE:Frozen] [HARD]` at `:23` and `:49`), `CLAUDE.md:48-56`; rule layout under `.claude/rules/` (all files under `moai/`).
- Config: `.moai/config/sections/git-strategy.yaml:1-113`.
- Searched, no commit/push/PR instruction found: `plan-auditor.md`, `sync-auditor.md`, `super-advisor.md`, `e2e-tester.md`; `manager-design.md:115,127` mention a DesignSync "push" that is not a repository operation.
- Not verified: how `moai update` treats edited agent, workflow, and `CLAUDE.md` files (AC-GITOWN-013 measures it); what consumes the `git-strategy.yaml` automation keys; whether Claude Code loads a rule file without `paths:` for every session (AC-GITOWN-011 probes it).

## §C Pre-flight and run-phase measurement tasks

1. Record `base_sha` (taken immediately before this SPEC's first run edit; run phases are executed one at a time in the order HOOKS, ENV, GITOWN, REVGATE) in `progress.md` §E.2; `export SCRATCH`; record the `protected_sha256:` block defined in `acceptance.md` Conventions (all `.claude/rules/moai/` files including `spec-workflow.md`, the hooks, `.moai/config/sections/*.yaml`, the `moai` binary).
2. Re-read the 14 files and re-run Scan S (`acceptance.md` Conventions) on the unchanged files; save the hit list as the RED baseline for AC-GITOWN-002 and -004. Correct the inventory in `progress.md` §E.2 if the files were regenerated.
3. Measure `moai update` (AC-GITOWN-013): save `moai update --help`, run the always-real scratch update with an isolated `HOME`, record per-file `cmp` and any user-level state created.
4. After the rule file exists, run the loading probe in AC-GITOWN-011 (fresh session in a scratch project) and record the result.
5. Record the expected review-gate noise: this SPEC leaves many uncommitted edits, and the MoAI Codex gate (`workflow.yaml:63`) reviews uncommitted changes at each Stop; the runtime caps consecutive Stop blocks at 8 (`hooks-system.md:213-215`). Expected, not a defect of this SPEC.

## §D Constraints

- Instruction-text edits, one new rule file, and `manager-git.md` frontmatter only; keep each agent's non-Git responsibilities as written.
- Use the single defined term "proposed repository action" and the label "Proposed repository action" for fenced blocks; use the exact prohibition sentence of REQ-GITOWN-004 (the acceptance greps match them literally).
- Do not edit `spec-workflow.md`, `AGENTS.md`, hooks, `git-strategy.yaml`, or the binary.
- Sub-agents run no `git`/`gh`; the coordinator runs every command in `acceptance.md`.
- `development_mode: tdd`: AC-GITOWN-001 to -004 and -007 to -010 are the tests (RED baseline first, then GREEN); AC-GITOWN-011 is the behavioral probe.

## §E Self-Verification

Run AC-GITOWN-001 to AC-GITOWN-013 in §F order (coordinator), recording verbatim output in `progress.md` §E.2. AC-GITOWN-011 is a Gap until a live probe exists; AC-GITOWN-013 is a measurement.

## §F Tasks (ordered by decision-reversibility, most likely to change first)

1. **Rewrite `manager-git.md`** as a proposal-only agent: new description (replacing lines 4-5), frontmatter without `Bash` and without `permissionMode: bypassPermissions` (lines 8, 12), body that produces a proposed repository action (files, commit subject/body, branch, commands) under the label "Proposed repository action" for every operation now at `:31-32,40-42,92-127,137,156-170`. Keep the commit-message conventions (`:46-57`) as the format of the proposal. Run AC-GITOWN-001, -002, -007, -008 for this file.
2. **Write the override rule** `.claude/rules/project/git-ownership.md`: frontmatter with `description:` only (no `paths:`); body of at most 40 lines (it loads in every session) stating orchestrator-only Git and GitHub operations, proposed-repository-action returns, precedence over the Route A/B text in `spec-workflow.md` (`:23-26`, `:30-47`, `:49-62`), and that other MoAI references to `manager-git` as executing Git (for example `e2e-tester.md:15`, `moai/SKILL.md:122,130,138,224`, `references/reference.md:24`, outside the edited set) now mean proposal-only. Run AC-GITOWN-005.
3. **Rewrite the other four agents** (`manager-develop.md:50,52,81,138,165-169,185,187,234`, `manager-docs.md:8,76,95`, `manager-spec.md:55,200`, `manager-lead.md:216`): replace each execute-instruction with "return a proposed repository action" and add the REQ-GITOWN-004 sentence. Status-transition ownership stays with the same agent; only the executing commit moves to the orchestrator. Run AC-GITOWN-001, -002, -007, -010.
4. **Rewrite the workflow files and `CLAUDE.md`** at the inventory lines (`run.md`, `plan.md`, `sync.md`, `sync/delivery.md` including Step 3.2 at `:213-330`, `plan/spec-assembly.md`, `run/task-decomposition.md`, `run/mode-orchestration.md`, `CLAUDE.md:53`). Keep Route A / Route B tier policy otherwise unchanged. Run AC-GITOWN-003, -004, -006, -010.
5. **Behavioral probe.** Run AC-GITOWN-011 (three trials).
6. **Commit (coordinator).** Stage the 14 paths by explicit pathspec, optionally in areas (agents, workflows, rule/CLAUDE.md). Run AC-GITOWN-009 and -012.
7. **Measure `moai update`.** Run AC-GITOWN-013; carry any negative result to the orchestrator.
8. **Sync-phase follow-up (manager-docs).** Note the orchestrator-only Git rule in `.moai/project/tech.md` or `structure.md` if either describes the workflow.

### Files to modify

| File | Lines (inventory) | Change |
|---|---|---|
| `.claude/agents/moai/manager-git.md` | 4, 5, 8, 12, 31-32, 40-42, 92-127, 137, 156-170 | proposal-only role; frontmatter without Bash/bypassPermissions; prohibition sentence |
| `.claude/agents/moai/manager-develop.md` | 50, 52, 81, 138, 165-169, 185, 187, 234 | propose commits; status change rides the orchestrator's commit |
| `.claude/agents/moai/manager-docs.md` | 8, 76, 95 | reword "NOT for ... git branch management"; propose the sync commit |
| `.claude/agents/moai/manager-spec.md` | 55, 200 | propose branch/PR and the mid-run commit |
| `.claude/agents/moai/manager-lead.md` | 216 | route push/PR to the orchestrator |
| `.claude/skills/moai/workflows/run.md` | 23, 37, 51, 152, 165 | phase owner wording; no git status instruction |
| `.claude/skills/moai/workflows/plan.md` | 25, 37, 97 | phase owner wording; Phase 12 row |
| `.claude/skills/moai/workflows/sync.md` | 25, 41, 52, 126 | phase owner wording |
| `.claude/skills/moai/workflows/sync/delivery.md` | 35-36, 38-46, 213-330, 448 | commit and delivery steps become proposals |
| `.claude/skills/moai/workflows/plan/spec-assembly.md` | 272-281, 312-314, 336, 340, 358, 385-391 | issue/branch/PR steps become proposals |
| `.claude/skills/moai/workflows/run/task-decomposition.md` | 292-312 | Route A / B Git steps become proposals |
| `.claude/skills/moai/workflows/run/mode-orchestration.md` | 78 | Phase 19 wording |
| `CLAUDE.md` | 53 | PR creation routing |
| `.claude/rules/project/git-ownership.md` | new | override rule |

## Risks

| ID | Risk | Evidence / Mitigation |
|---|---|---|
| R1 | `moai update` regenerates agent, workflow, and `CLAUDE.md` files and discards the edits. | The binary embeds `templates/.claude/...`; AC-GITOWN-013 measures it; the override rule outside `moai/` is expected to persist. |
| R2 | The override rule is read but the Frozen text still wins in a model's reading. | Text-only change; AC-GITOWN-011 probes behavior; a technical guard is out of scope. |
| R3 | Rewrites drift from upstream wording and make later merges noisy. | Minimal edits tied to the defined term and the Scan S label so they are greppable. |
| R4 | Removing `Bash` and `bypassPermissions` from `manager-git` breaks a workflow that relied on them. | Its remaining output is text (proposals); AC-GITOWN-011 exercises it; revert is a one-line frontmatter change. |
| R5 | A text-only change does not stop a non-edited agent from running Git through `Bash`. | Declared out of scope (Exclusions). |
| R6 | A 14-file edit across managed files is large to review. | ACs are per file; the coordinator may commit by area. |
| R7 | Scan S flags prose mentions (for example `manager-develop.md:234`, `sync/delivery.md:46`); rewording them is intended but may feel pedantic. | Intended: the AC is meant to fail while imperative Git text remains. |

## §G Anti-Patterns

- Do not add a carve-out that lets an agent run `git` or `gh`, even read-only (`AGENTS.md:13`).
- Do not paraphrase the defined term, the label, or the prohibition sentence; the greps match them literally.
- Do not edit `AGENTS.md` or `spec-workflow.md`; the override rule is the mechanism.
- Do not widen the edit to agents or files that have no Git instruction.
- Do not `git add -A`; stage by pathspec.

## MX Tag Plan

None. No source file with `@MX` annotations is touched.

## §H Cross-References

- `AGENTS.md:3-15`, `.claude/agents/moai/manager-git.md:4-5,8,12`, `.claude/rules/moai/workflow/spec-workflow.md:23-26,49-62`, `.moai/config/sections/git-strategy.yaml:5,48,61-63`.
- SPEC-HOOKS-001 and SPEC-ENV-001 (same `moai update` measurement), SPEC-REVGATE-001 (depends on this SPEC).

## Deferred (no decision needed to start)

- `git-strategy.yaml` automation keys (`auto_commit: true` at `:61`, `push_to_remote: true` at `:48`): not edited; their consumer was not verified. Follow-up SPEC if automatic commits are found to act outside the orchestrator.
- A technical guard against sub-agent `git`/`gh` (for example a PreToolUse rule): follow-up SPEC.
- The `gui`/`backend_*` roster of `AGENTS.md:7-11` versus the MoAI agents: note only.

## Decisions recorded before Kickoff Approval

- Decided 2026-10-18 by the user: remove `Bash` from `tools` and `permissionMode: bypassPermissions` from `manager-git.md` (REQ-GITOWN-005, AC-GITOWN-008 stay in scope). No open decisions remain.
