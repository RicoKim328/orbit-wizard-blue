---
id: SPEC-GITOWN-001
title: "Align MoAI agent and workflow Git instructions with orchestrator-only Git ownership"
version: "0.3.0"
status: draft
created: 2026-10-18
updated: 2026-10-18
author: Rico
priority: P1
phase: "v0.1.1 target"
module: ".claude/agents/moai"
lifecycle: spec-anchored
tags: "git, ownership, agents, workflows, orchestrator, pull-request, agents-md, rules, tooling"
tier: M
---

# SPEC-GITOWN-001: Align MoAI agent and workflow Git instructions with orchestrator-only Git ownership

## HISTORY

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1.0 | 2026-10-18 | Rico | Initial draft (Tier S) |
| 0.2.0 | 2026-10-18 | Rico | Iteration 2 (plan-audit findings X-1..X-5, X-7..X-9, G-1..G-8): Tier M with acceptance.md; coordinator = MoAI orchestrator; manager-git kept as proposal-only; `spec-workflow.md` (Frozen) left unedited and overridden by a new project rule; complete conflict inventory; negative scan ACs; carve-out AC; single tracking scope |
| 0.3.0 | 2026-10-18 | Rico | Iteration 3 (re-audit G2-1..G2-6, C-1..C-3): sha256 record replaces `git diff` on untracked protected files; inventory adds `manager-docs.md:8`, `run.md:165`, `plan/spec-assembly.md:336`; Scan S verb list extended; rule-layout sentence corrected; override rule size-bounded and states that other `manager-git` references now mean proposal-only; contiguous `base_sha`; defined scratch copy |

## 1. Context

This repository's `AGENTS.md` (read in this worktree) gives Git and GitHub ownership to one party. Line 13: "Only Astra may perform Git or GitHub operations. Sub-agents must not run `git` or `gh` commands (including read-only commands), access or modify `.git`, or perform repository operations through scripts, APIs, connectors, or other indirect methods. This includes staging, commits, branches, worktrees, fetch/pull/push, merges, tags, and pull requests. Ask Astra for any repository information or action needed." Line 5 names Astra as the primary coordinator; line 15 forbids beginning implementation without a concrete assignment from Astra.

User decision (iteration 2): Astra is the MoAI main session, the orchestrator. `manager-git` is kept but becomes proposal-only. In this SPEC "the orchestrator" means Astra.

The MoAI-managed agent and workflow text, untracked in the primary checkout (`/home/rico/Desktop/Project/orbit-wizard-blue`) and absent from this worktree, instructs sub-agents to do exactly what line 13 prohibits. The Codex review gate reported the conflict for `manager-git.md`, as relayed by the coordinator; it is also upstream issue https://github.com/modu-ai/moai-adk/issues/1827 item 5 (open, opened 2026-10-17, read through a WebFetch summary, which says the reporter did not reproduce it). Resolution direction (user decision): project-local hardening, tracked in git, in parallel with the upstream tracker. Expected behavior: sub-agents return a proposed repository action to the orchestrator instead of executing it.

Reproduced by author: not applicable as a runtime bug; the conflict was established by reading. Line numbers were read on 2026-10-18; the plan-audit independently re-checked the original inventory and added the lines marked (audit). A regex re-scan of the named files for `git|gh` followed by a repository verb was run by the author and is the basis of the additions.

Definitions. A proposed repository action is the text an agent returns in place of acting: the file list, the commit subject and body, the target branch, and the exact commands, for the orchestrator to review and run. In edited files it appears under the label "Proposed repository action".

### Conflict inventory (instructions that direct a sub-agent to run Git or GitHub operations)

Agent definitions (`.claude/agents/moai/`):

| File:line | What it says |
|---|---|
| `manager-git.md:4,5` | "Use PROACTIVELY for commits, branches, PR management, merges, releases, and version control."; "manager-develop/manager-docs perform commits only; push + PR is always delegated to manager-git" |
| `manager-git.md:8,12` | `tools` includes `Bash`; `permissionMode: bypassPermissions` |
| `manager-git.md:31-32` | `gh pr create` / `gh pr merge` |
| `manager-git.md:40-42` | checkpoint `git tag`, `git tag -l`, `git reset --hard` |
| `manager-git.md:92,96-99,104-105,110-114,119-122,125,127,137` | Late-Branch pattern: `git rev-list`, `git checkout main && git pull`, `git add`, `git commit`, `git switch -c`, `git push -u`, `gh pr create`, `gh pr merge`, `git fetch`, `git reset --hard`, push hold, recovery (audit: 96, 119-120, 127) |
| `manager-git.md:156,160-162,168-170` | read-only `git fetch`/`git status`/`gh pr checks` batch; `git fetch origin` → `git pull`; rebase; `gh pr ready`/`checks`/`merge` (audit: 160-162) |
| `manager-develop.md:50,52` | autofix loop counted "per PR push"; commit strategy (new commit per patch, force-push and `--amend` prohibited) |
| `manager-develop.md:81` | routing table row "Git operations \| manager-git" (audit) |
| `manager-develop.md:138` | "Commit changes, update SPEC status" |
| `manager-develop.md:165-169,185,187` | owns the first run-phase (M1) commit that carries the `draft → in-progress` status change |
| `manager-develop.md:234` | invoke the worktree skill when operating inside an isolated git worktree (read as context; the skill itself is out of scope) |
| `manager-docs.md:8` | description "NOT for: ... git branch management" (Scan S flags it; reworded in the rewrite) |
| `manager-docs.md:76` | owns the "single sync commit" that carries the `completed` transition |
| `manager-docs.md:95` | CHANGELOG paths verified "before committing" |
| `manager-spec.md:55` | "Git branch/PR: Delegate to manager-git" |
| `manager-spec.md:200` | mid-run edit "committed in a separate commit attributed to this agent" |
| `manager-lead.md:216` | "PR creation → orchestrator hands off to `manager-git` (Tier L / `--pr`) or handles Tier S/M push+PR directly" |

Workflow and project text:

| File:line | What it says |
|---|---|
| `.claude/skills/moai/workflows/run.md:23,37,51,152,165` | `manager-git` listed as agent and phase owner; "git operations (Phase 19)"; "surfaced via git status"; evaluator note mentioning `git status` at `:165` |
| `.claude/skills/moai/workflows/plan.md:25,37,97` | `manager-git` listed; owns worktree/branch creation; Phase 12 "gh issue create" row |
| `.claude/skills/moai/workflows/sync.md:25,41,52,126` | `manager-git` listed; owns PR creation; "Phase 13 Git Operations" |
| `.claude/skills/moai/workflows/sync/delivery.md:35-36,38-42,46` | Route A: "manager-docs creates the single sync commit directly on `main`"; Route B: "manager-git creates the same single sync commit"; both stage, commit, "Verify commit with git log"; "git commit operations" context |
| `.claude/skills/moai/workflows/sync/delivery.md:213-330` | Step 3.2 (audit): `git push -u origin`, `gh pr list`, `gh pr create`, `git push origin main`/`develop`, `gh pr ready`, `git checkout ... && git pull`, `gh pr checks`, `gh pr view`, `gh pr merge --squash --delete-branch` (lines 229-231, 241, 253, 262, 267, 272, 278, 289, 297-298, 316-318, 328-330) |
| `.claude/skills/moai/workflows/sync/delivery.md:448` | "syncs based on git diff" |
| `.claude/skills/moai/workflows/plan/spec-assembly.md:272-276,280-281,312-314,336,340,358,385-391` | `manager-git` subagent creates the GitHub issue (`gh issue create`, `gh issue comment`), creates the branch, sets upstream, creates a draft PR (audit: 281, 312-314; `:336` is branch-creation prose that Scan S flags) |
| `.claude/skills/moai/workflows/run/task-decomposition.md:292-301` | Route A: manager-develop "Stage[s] ... Commit[s] directly to `main` ... Push[es] the commit(s) to `main`" |
| `.claude/skills/moai/workflows/run/task-decomposition.md:303-312` | Route B: "Agent: manager-git subagent" creates branch, commits, opens a PR |
| `.claude/skills/moai/workflows/run/mode-orchestration.md:78` | "Phase 19: manager-git created commits (branch or direct)" |
| `CLAUDE.md:53` | "PR creation (Tier L OR `--pr`) → `manager-git`" |

Frozen-zone rule text, NOT edited (user decision 3): `.claude/rules/moai/workflow/spec-workflow.md:23` carries `[ZONE:Frozen] [HARD]`; Route A at `:25` ("manager-develop commits and pushes directly to `main`") and Route B at `:26` ("`manager-git` creates a feature branch and opens a PR per phase (`gh pr create`)"); the Route A/B tables at `:30-47` and the step rules at `:49-62` (Frozen at `:49`; audit: 34-36, 51, 62) repeat commit/push/PR steps. A new project-level rule overrides them (REQ-GITOWN-003).

Configuration that may enable the same behavior without any agent text (not edited): `.moai/config/sections/git-strategy.yaml:5` (`mode: "personal"`), `:48` (`push_to_remote: true`), `:61` (`auto_commit: true`), with `:62-63` `auto_pr: false` and `auto_push: false`. Which code consumes these keys was not verified.

Rule-file layout and loading (read 2026-10-18): all existing rules are under `.claude/rules/moai/<area>/`; most carry YAML frontmatter with `paths:` globs that scope when they load, while always-loaded rules such as `moai-constitution.md` start with an H1 and have no frontmatter. A rule file without `paths:` is not path-scoped. The override is placed outside the `moai/` namespace, at `.claude/rules/project/git-ownership.md`, without `paths:`.

Also noted, out of scope: `AGENTS.md:7-11` names sub-agents `gui`, `backend_data`, `backend_orbit`; the only MoAI agents in `.claude/agents/moai/` are `e2e-tester`, `manager-design`, `manager-develop`, `manager-docs`, `manager-git`, `manager-lead`, `manager-spec`, `plan-auditor`, `super-advisor`, `sync-auditor`. The `moai-workflow-worktree` skill is not reviewed.

Edited set (14 files, 13 edited and 1 new): the five agents above; `run.md`, `plan.md`, `sync.md`, `sync/delivery.md`, `plan/spec-assembly.md`, `run/task-decomposition.md`, `run/mode-orchestration.md` under `.claude/skills/moai/workflows/`; `CLAUDE.md`; and the new `.claude/rules/project/git-ownership.md`.

## 2. Requirements (GEARS)

### REQ-GITOWN-001 — Agents propose instead of executing
Each of the agent definitions `manager-git.md`, `manager-develop.md`, `manager-docs.md`, `manager-spec.md`, and `manager-lead.md` shall direct its agent to return a proposed repository action to the orchestrator for every staging, commit, branch, push, merge, tag, worktree, and PR or issue operation it would otherwise perform, shall describe `manager-git` as a proposal-only agent, and shall contain no imperative `git` or `gh` repository command outside a block labeled "Proposed repository action".

### REQ-GITOWN-002 — Workflows and project text route Git steps to the orchestrator
The workflow files `run.md`, `plan.md`, `sync.md`, `sync/delivery.md`, `plan/spec-assembly.md`, `run/task-decomposition.md`, and `run/mode-orchestration.md`, and `CLAUDE.md`, shall describe each commit, branch, push, PR, and issue step as "the agent returns a proposed repository action and the orchestrator executes it", shall name no sub-agent as the executor of that step, and shall contain no imperative `git` or `gh` repository command outside a block labeled "Proposed repository action"; `.claude/rules/moai/workflow/spec-workflow.md` shall remain unmodified.

### REQ-GITOWN-003 — A project rule overrides the Frozen Route text
The repository shall contain `.claude/rules/project/git-ownership.md`, without a `paths:` key, stating that Git and GitHub operations belong to the orchestrator only, that sub-agents return proposed repository actions, that this rule takes precedence over the Route A and Route B commit, push, branch, and PR text in `.claude/rules/moai/workflow/spec-workflow.md`, and that other MoAI references to `manager-git` as executing Git operations now mean proposal-only; the file shall be at most 40 lines long because it loads in every session.

### REQ-GITOWN-004 — Prohibition is stated in each affected agent
Each agent definition named in REQ-GITOWN-001 shall contain the sentence "Only the orchestrator (Astra) runs git or gh; ask the orchestrator for repository information or actions." in its body.

### REQ-GITOWN-005 — manager-git holds no execution authority
The frontmatter of `manager-git.md` shall not list `Bash` in `tools` and shall not set `permissionMode: bypassPermissions`.

### REQ-GITOWN-006 — Ownership rule is not weakened
The change shall leave `AGENTS.md` unmodified, and no edited file shall contain wording that lets a sub-agent run `git` or `gh`, including read-only commands.

### REQ-GITOWN-007 — Exactly the edited set is tracked and changed
The repository shall track the 14 files of the edited set in git, and the change shall modify no other tracked file, hook, configuration file, or the `moai` binary.

## 3. Acceptance Criteria

Tier M: the acceptance criteria are in `acceptance.md` (AC-GITOWN-001 to AC-GITOWN-013), written as Given-When-Then. Mapping:

| REQ | AC |
|---|---|
| REQ-GITOWN-001 | AC-GITOWN-001, AC-GITOWN-002, AC-GITOWN-011 |
| REQ-GITOWN-002 | AC-GITOWN-003, AC-GITOWN-004, AC-GITOWN-006 |
| REQ-GITOWN-003 | AC-GITOWN-005, AC-GITOWN-006, AC-GITOWN-011 |
| REQ-GITOWN-004 | AC-GITOWN-007 |
| REQ-GITOWN-005 | AC-GITOWN-008 |
| REQ-GITOWN-006 | AC-GITOWN-009, AC-GITOWN-010, AC-GITOWN-011 |
| REQ-GITOWN-007 | AC-GITOWN-012, AC-GITOWN-013 (measurement) |

The coordinator (orchestrator) runs every verification command in `acceptance.md`; implementers only edit files and report.

## 4. Exclusions

### Out of Scope — Enforcement
- No hook, permission rule, or `moai` binary change that technically blocks `git`/`gh` from sub-agents; this SPEC changes instructions, one rule file, and one agent's frontmatter only.
- No change to `.moai/config/sections/git-strategy.yaml` (its automation keys are not edited; their consumer was not verified).

### Out of Scope — The Frozen rule and AGENTS.md
- No edit of `.claude/rules/moai/workflow/spec-workflow.md` and no edit of `AGENTS.md`.
- No creation or renaming of the `gui`, `backend_data`, and `backend_orbit` sub-agents that `AGENTS.md:7-11` names and that do not exist as MoAI agents.

### Out of Scope — Other instruction content
- No change to agent responsibilities other than repository operations (SPEC authoring, implementation, documentation, audit duties stay as written), no change to the Route A / Route B tier policy beyond who executes the Git steps, and no change to the `moai-workflow-worktree` skill.

### Out of Scope — Upstream
- No edit of upstream issue #1827 and no upstream patch.
