---
description: Orchestrator-only Git and GitHub ownership. Sub-agents return proposed repository actions; this rule overrides the Route A/B Git execution text in spec-workflow.md.
---

# Git Ownership (project rule)

Only the orchestrator runs git or gh; ask the orchestrator for repository information or actions.

In this project the orchestrator is the MoAI main session. Sub-agents run no `git` or `gh` command, including read-only ones, and perform no repository operation through scripts, APIs, or other indirect means. This covers staging, commits, branches, worktrees, fetch, pull, push, merges, tags, and pull requests or issues.

## Proposed repository action

A sub-agent that would otherwise perform a repository operation returns a proposed repository action instead: the file list, the commit subject and body, the target branch, and the exact commands, in a fenced block preceded by the label "Proposed repository action". The orchestrator reviews it and runs it.

Status-transition ownership is unchanged. The agent that owns a transition still writes the frontmatter change; only the commit that carries it moves to the orchestrator.

## Precedence

This rule takes precedence over the Route A and Route B commit, push, branch, and PR text in `.claude/rules/moai/workflow/spec-workflow.md` (the route definitions under SPEC Phase Discipline, the Route A / Route B tables, the step-ordering rules, and the Late-branch closure step). Read that text as describing which repository actions happen and in what order; the orchestrator executes each of them.

- Route A: where it says manager-develop commits and pushes to `main`, manager-develop returns a proposed repository action and the orchestrator commits and pushes.
- Route B: where it says `manager-git` creates a feature branch and opens a PR, `manager-git` drafts the branch and PR as a proposed repository action and the orchestrator runs it.

`manager-git` is proposal-only. Every other MoAI reference to `manager-git` as executing Git operations, for example `.claude/agents/moai/e2e-tester.md:15`, `.claude/skills/moai/SKILL.md:122,130,138,224`, and `.claude/skills/moai/references/reference.md:24`, now means proposal-only: `manager-git` proposes and the orchestrator executes.
