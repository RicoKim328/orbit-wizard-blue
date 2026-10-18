# SPEC-GITOWN-001 (compact)

Auto-generated summary of `spec.md` v0.3.0, `acceptance.md` and `plan.md` (Tier M): requirements, acceptance criteria, files to modify, exclusions. `spec.md` and `acceptance.md` are authoritative.

`AG` = `.claude/agents/moai`; `WF` = `.claude/skills/moai/workflows`; `<base_sha>` = `git rev-parse HEAD` taken immediately before this SPEC's first run edit (run phases one at a time: HOOKS, ENV, GITOWN, REVGATE); `protected_sha256:` (rules, hooks, `.moai/config/sections`, the `moai` binary) recorded there and checked with `sha256sum -c`. The coordinator (orchestrator, Astra) runs every command in `acceptance.md`; ACs marked [coordinator-run] call git, run `moai`, or open live sessions. Scan S = awk scan for `git|gh` plus a repository verb outside fenced blocks labeled "Proposed repository action".

## Conflict

`AGENTS.md:13`: only Astra performs Git/GitHub operations; sub-agents must not run `git`/`gh`, even read-only. User decisions: Astra = the MoAI orchestrator; `manager-git` is kept as proposal-only; `spec-workflow.md` (Frozen) is not edited and is overridden by a new rule. Conflicting text (read 2026-10-18; full list in `spec.md` §1): `manager-git.md:4,5,8,12,31-32,40-42,92-127,137,156-170`; `manager-develop.md:50,52,81,138,165-169,185,187,234`; `manager-docs.md:8,76,95`; `manager-spec.md:55,200`; `manager-lead.md:216`; `run.md:23,37,51,152,165`; `plan.md:25,37,97`; `sync.md:25,41,52,126`; `sync/delivery.md:35-46,213-330,448`; `plan/spec-assembly.md:272-281,312-314,336,340,358,385-391`; `run/task-decomposition.md:292-312`; `run/mode-orchestration.md:78`; `CLAUDE.md:53`. Untouched: `spec-workflow.md:23-26,30-62`. Reproduced by author: not applicable (established by reading).

## Requirements

- **REQ-GITOWN-001**: The five agent definitions shall direct their agents to return a proposed repository action to the orchestrator for every Git/GitHub operation, describe `manager-git` as proposal-only, and contain no imperative `git`/`gh` repository command outside a labeled block.
- **REQ-GITOWN-002**: The seven workflow files and `CLAUDE.md` shall route each such step to the orchestrator, name no sub-agent as executor, and contain no imperative command outside a labeled block; `spec-workflow.md` stays unmodified.
- **REQ-GITOWN-003**: `.claude/rules/project/git-ownership.md` (no `paths:`) shall state orchestrator-only Git/GitHub operations and precedence over the Route A/B text in `spec-workflow.md`.
- **REQ-GITOWN-004**: Each of the five agents shall contain "Only the orchestrator (Astra) runs git or gh; ask the orchestrator for repository information or actions."
- **REQ-GITOWN-005**: `manager-git.md` frontmatter shall not list `Bash` in `tools` nor set `permissionMode: bypassPermissions`.
- **REQ-GITOWN-006**: `AGENTS.md` stays unmodified and no edited file lets a sub-agent run `git`/`gh`.
- **REQ-GITOWN-007**: Exactly the 14 files of the edited set are tracked and changed; nothing else.

## Acceptance Criteria

| AC | Check | Pass condition |
|---|---|---|
| AC-GITOWN-001 | `grep -L -F 'proposed repository action'` on the five agents; `grep -c -F -e` of listed old strings | prints nothing; `0` per old string; manager-git described as proposal-only |
| AC-GITOWN-002 | Scan S on the five agents | prints nothing (RED baseline lists `manager-git.md` lines) |
| AC-GITOWN-003 | `grep -L -F 'proposed repository action'` on the 7 workflows + `CLAUDE.md`; `grep -c -F -e` of listed old strings | prints nothing; `0` per old string |
| AC-GITOWN-004 | Scan S on the 7 workflows + `CLAUDE.md` | prints nothing (RED baseline lists `sync/delivery.md` and `spec-assembly.md` lines) |
| AC-GITOWN-005 | rule file exists, `grep -c '^paths:'`, required phrases, `wc -l`, `proposal-only`, Route A/B mentions | `exit=0`, `0`, each phrase count at least `1`, at most 40 lines |
| AC-GITOWN-006 | `sha256sum -c` of the protected record (includes `spec-workflow.md`) | `OK` for every recorded file |
| AC-GITOWN-007 | `grep -L -F 'Only the orchestrator (Astra) runs git or gh'` on the five agents | prints nothing |
| AC-GITOWN-008 | frontmatter of `manager-git.md` piped to `grep -c -E 'Bash\|bypassPermissions'` | `0` |
| AC-GITOWN-009 | `git diff --quiet <base_sha>..HEAD -- AGENTS.md` | `exit=0` |
| AC-GITOWN-010 | carve-out phrase grep over the edited files | `exit=1` |
| AC-GITOWN-011 | three-trial probe of `manager-git` in a scratch repo (no remote, no `gh` auth); rule-loading question | proposals/declines only; repo unchanged (`rev-list --count` still `1`, file untracked); answer cites the rule; Gap if no live session |
| AC-GITOWN-012 | `git ls-files --error-unmatch`, `git status --porcelain`, name-only diffs vs `<base_sha>`; `git diff` on `AGENTS.md`; `sha256sum -c` of the protected record | the 14 paths tracked, clean, and the diff lists exactly them; nothing for `AGENTS.md`; every protected file `OK` |
| AC-GITOWN-013 | real `moai update --templates-only --no-hooks --yes` in a scratch copy with isolated `HOME`; `cmp` per file | verbatim output and `preserved`/`overwritten-or-merged` per file; any difference is a Gap |

## Files to Modify

The 14 files of the edited set at the inventory lines above (`plan.md` Files to modify); the new file is `.claude/rules/project/git-ownership.md`.

## Exclusions

### Out of Scope — Enforcement
- No hook, permission rule, or binary change that technically blocks `git`/`gh`; no change to `git-strategy.yaml`.

### Out of Scope — The Frozen rule and AGENTS.md
- No edit of `spec-workflow.md` or `AGENTS.md`; no creation of `gui`, `backend_data`, `backend_orbit`.

### Out of Scope — Other instruction content
- Non-Git responsibilities of the agents, the Route A / B tier policy, and the `moai-workflow-worktree` skill stay as written.

### Out of Scope — Upstream
- No edit of upstream issue #1827 and no upstream patch.
