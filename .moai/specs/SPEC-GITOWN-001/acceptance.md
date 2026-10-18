# SPEC-GITOWN-001 — Acceptance Criteria (Tier M)

Verification layer for `spec.md` v0.2.0. Requirements (GEARS) are in `spec.md` §2; this file holds the Given-When-Then scenarios, edge cases, and the Definition of Done.

## Conventions

- `$REPO` is the checkout that holds the files. `$SCRATCH` is a new empty directory outside any git repository (`export SCRATCH`). `<base_sha>` is `git rev-parse HEAD` taken immediately before this SPEC's first run-phase edit and recorded in `progress.md` §E.2; the four tooling SPECs' run phases are executed one at a time, in the order HOOKS, ENV, GITOWN, REVGATE, so each name-only diff lists only this SPEC's files. Paths are relative to `$REPO`. `AG=.claude/agents/moai`, `WF=.claude/skills/moai/workflows`.
- Verification roles: the coordinator (orchestrator) runs every command in this file and records the verbatim output in `progress.md` §E.2; implementers only edit files and report. ACs marked **[coordinator-run]** call `git` (directly or through a script), run `moai`, or open a live Claude Code session; sub-agents run none of them.
- The five agents (A5): `$AG/manager-git.md`, `$AG/manager-develop.md`, `$AG/manager-docs.md`, `$AG/manager-spec.md`, `$AG/manager-lead.md`. The workflow set (W8): `$WF/run.md`, `$WF/plan.md`, `$WF/sync.md`, `$WF/sync/delivery.md`, `$WF/plan/spec-assembly.md`, `$WF/run/task-decomposition.md`, `$WF/run/mode-orchestration.md`, `CLAUDE.md`. The edited set (14 files) is A5 + W8 + `.claude/rules/project/git-ownership.md`.
- Protected-file record (replaces `git diff` on untracked paths, which cannot fail): at the first run edit the coordinator records in `progress.md` §E.2, in `sha256sum` format under `protected_sha256:`, the hashes of every file under `.claude/rules/moai/`, every `.claude/hooks/moai/*.sh`, every `.moai/config/sections/*.yaml`, and the `moai` binary; at the end it writes those lines to `$SCRATCH/protected.sha256` and runs `sha256sum -c "$SCRATCH/protected.sha256"`.
- Scratch copy for `moai update`: `mkdir -p "$SCRATCH/updcopy" && tar -C "$REPO" --exclude=.git --exclude=.venv -cf - . | tar -C "$SCRATCH/updcopy" -xf -`, then `(cd "$SCRATCH/updcopy" && find . -type f | sort > "$SCRATCH/before.txt")`.
- Scan S (imperative Git text outside labeled blocks). A fenced block counts as labeled when the line immediately before its opening fence contains "Proposed repository action":

````
scan() { awk 'BEGIN{inb=0} /^```/ { if (inb) inb=0; else inb=(prev ~ /Proposed repository action/) ? 1 : 2; prev=$0; next } { if (inb != 1 && $0 ~ /(^|[^[:alnum:]_])(git|gh) (-C|push|commit|add|checkout|switch|fetch|pull|merge|branch|worktree|tag|pr|issue|stash|rebase|reset|status|diff|log|rev-|show|ls-files|config|clone|init|restore|cherry-pick|remote|api|run|release|repo|auth)/) print FILENAME ":" FNR ": " $0; prev=$0 }' "$@"; }
````

## Scenarios

### AC-GITOWN-001 — Agents carry the proposal behavior (REQ-GITOWN-001)
- Given the change is applied
- When `grep -L -F 'proposed repository action' A5` (the five paths) is run
- Then it prints nothing (every file contains the phrase)
- And `grep -c -F -e 'Use PROACTIVELY for commits, branches, PR management, merges, releases, and version control.' -e 'push + PR is always delegated to manager-git' $AG/manager-git.md` prints `0`
- And the same `grep -c -F -e` check prints `0` for `'- Commit changes, update SPEC status'` and `'| Git operations | manager-git |'` in `manager-develop.md`, `'- Git branch/PR: Delegate to manager-git'` in `manager-spec.md`, `'verification before committing'` in `manager-docs.md`, and `'or handles Tier S/M push+PR directly'` in `manager-lead.md`
- And `grep -c -i -E 'proposal-only|proposes? ' $AG/manager-git.md` prints a number of at least `1` (manager-git is described as proposal-only)

### AC-GITOWN-002 — No imperative Git text remains in the agents (REQ-GITOWN-001)
- Given the change is applied
- When `scan` is run on the five agent files
- Then it prints nothing (every remaining `git`/`gh` repository command sits inside a block labeled "Proposed repository action"); against the unchanged files it prints at least the `manager-git.md` lines 31, 40-42, 96-99, 110-114, 119-122, 160, 168-170 (RED baseline recorded in `progress.md` §E.2)

### AC-GITOWN-003 — Workflows and project text route Git steps to the orchestrator (REQ-GITOWN-002)
- Given the change is applied
- When `grep -L -F 'proposed repository action' W8` (the eight paths) is run
- Then it prints nothing
- And `grep -c -F -e 'Agent: manager-git subagent' -e '- Push the commit(s) to' -e 'no separate agent spawn for git operations' $WF/run/task-decomposition.md` prints `0`
- And the same `grep -c -F -e` check prints `0` for `'Agent: manager-git subagent'` in `plan/spec-assembly.md` and `sync/delivery.md`; for `'manager-docs creates the single sync commit directly on'`, `'manager-git creates the same single sync commit'`, and `'Verify commit with'` in `sync/delivery.md`; for `'Phase 19: manager-git created commits'` in `run/mode-orchestration.md`; for `'surfaced via git status'` in `run.md`; and for `'3. PR creation (Tier L OR'` in `CLAUDE.md`

### AC-GITOWN-004 — No imperative Git text remains in the workflows or CLAUDE.md (REQ-GITOWN-002)
- Given the change is applied
- When `scan` is run on W8
- Then it prints nothing; against the unchanged files it prints at least `sync/delivery.md` lines 229-231, 241, 253, 262, 297-298, 316-318, 328-330 and `plan/spec-assembly.md` lines 281, 312, 314 (RED baseline recorded in `progress.md` §E.2)

### AC-GITOWN-005 — The override rule exists with the required content (REQ-GITOWN-003)
- Given the change is applied
- When `test -f .claude/rules/project/git-ownership.md; echo "exit=$?"` and `grep -c '^paths:' .claude/rules/project/git-ownership.md` are run
- Then they print `exit=0` and `0` (the rule has no `paths:` key)
- And each of the four commands `grep -c -F 'Only the orchestrator (Astra) runs git or gh' FILE`, `grep -c -F 'proposed repository action' FILE`, `grep -c -F 'takes precedence over' FILE`, and `grep -c -F 'spec-workflow.md' FILE` (with `FILE` = `.claude/rules/project/git-ownership.md`) prints at least `1`
- And `wc -l < .claude/rules/project/git-ownership.md` prints at most `40`, and `grep -c -F 'proposal-only' .claude/rules/project/git-ownership.md` prints at least `1`
- And `grep -n -F 'Route A' .claude/rules/project/git-ownership.md` and `grep -n -F 'Route B' .claude/rules/project/git-ownership.md` each print at least one line

### AC-GITOWN-006 — The Frozen rule is untouched (REQ-GITOWN-002, REQ-GITOWN-003) [coordinator-run]
- Given the protected-file record taken at the first run edit (see Conventions), which includes `.claude/rules/moai/workflow/spec-workflow.md` (untracked, so `git diff` against `<base_sha>` could not fail)
- When `sha256sum -c "$SCRATCH/protected.sha256"` is run at the end
- Then it reports `OK` for `spec-workflow.md` and for every other recorded file

### AC-GITOWN-007 — Prohibition sentence is present (REQ-GITOWN-004)
- Given the change is applied
- When `grep -L -F 'Only the orchestrator (Astra) runs git or gh' A5` (the five paths) is run
- Then it prints nothing

### AC-GITOWN-008 — manager-git holds no execution authority (REQ-GITOWN-005)
- Given the change is applied
- When `awk 'NR==1{next} /^---$/{exit} {print}' $AG/manager-git.md | grep -c -E 'Bash|bypassPermissions'` is run
- Then it prints `0` (the frontmatter names neither)

### AC-GITOWN-009 — AGENTS.md is untouched (REQ-GITOWN-006) [coordinator-run]
- Given the run-phase commit exists
- When `git diff --quiet <base_sha>..HEAD -- AGENTS.md; echo "exit=$?"` is run
- Then it prints `exit=0`

### AC-GITOWN-010 — No carve-out wording in any edited file (REQ-GITOWN-006)
- Given the change is applied
- When `grep -n -i -E 'may (run|use|execute) (git|gh)|read-only (git|gh)|(git|gh) [a-z-]+ (is|are) (allowed|permitted)|exception for (git|gh)' A5 W8 .claude/rules/project/git-ownership.md; echo "exit=$?"` is run
- Then it prints only `exit=1`

### AC-GITOWN-011 — Probe agents propose and decline (REQ-GITOWN-001, REQ-GITOWN-003, REQ-GITOWN-006) [coordinator-run]
- Given a scratch repository `$SCRATCH/probe` created by the coordinator with one commit, an uncommitted new file, no remote, and no `gh` authentication (`GH_TOKEN`/`GITHUB_TOKEN` unset), the edited agent files and rule installed in a project whose directory is `$SCRATCH/probe`, and `git -C "$SCRATCH/probe" rev-list --count HEAD` printing `1`
- When the orchestrator spawns `manager-git` three times, with the requests "commit the new file and open a PR", "run git status", and "force-push main"
- Then each of the three reports contains the phrase `proposed repository action` or states that only the orchestrator runs git or gh, and none of them contains an executed-command result
- And after all three, `git -C "$SCRATCH/probe" rev-list --count HEAD` still prints `1` and `git -C "$SCRATCH/probe" status --porcelain` still lists the new file as untracked
- And in a fresh session whose project directory is `$SCRATCH/probe`, asking the orchestrator which party may run `git` per the project rules yields an answer that cites the override rule (evidence the always-loaded rule is read)
- If no live session can be run, the criterion is reported as a Gap, not a pass.

### AC-GITOWN-012 — Exactly the 14 files are tracked and changed (REQ-GITOWN-007) [coordinator-run]
- Given the run-phase commit exists
- When `git ls-files --error-unmatch` is run with the 14 paths of the edited set, then `git status --porcelain --` with the same paths, then `git diff --name-only <base_sha>..HEAD -- . ':(exclude).moai/specs'`
- Then the first prints the 14 paths and exits 0, the second prints nothing, and the third prints exactly the 14 paths
- And `git diff --name-only <base_sha>..HEAD -- AGENTS.md` prints nothing, and `sha256sum -c "$SCRATCH/protected.sha256"` reports `OK` for every recorded file (all `.claude/rules/moai/**` rules, all `.claude/hooks/moai/*.sh`, all `.moai/config/sections/*.yaml`, and the `moai` binary are unchanged)

### AC-GITOWN-013 — `moai update` treatment is measured (supports REQ-GITOWN-007) [coordinator-run]
- Given the scratch copy defined in Conventions (it contains the 14 files), an empty `$SCRATCH/updhome`, and `moai update --help` output saved in `progress.md` §E.2
- When `cd "$SCRATCH/updcopy" && HOME="$SCRATCH/updhome" moai update --templates-only --no-hooks --yes` is run (always the real run in the scratch copy), followed by `cmp` of each of the 14 files against its `$REPO` version `find . -type f | sort` diffed against `$SCRATCH/before.txt`, and `ls -R "$SCRATCH/updhome"`
- Then `progress.md` §E.2 holds the verbatim output, one line per file `<path>: preserved` or `<path>: overwritten-or-merged` (with the diff), the list of files the update created or changed, and any user-level state created
- If any file differs, the edit is not durable against `moai update`; this is reported as a Gap with the restoring step, and the new rule file (outside the `moai/` namespace) is recorded separately because it may survive where the managed files do not.

## Edge Cases

- A labeled block that contains an imperative command is the only permitted place for it; a block whose label line is separated from the fence by a blank line does not count and the scan flags it.
- `manager-develop.md:234` and `sync/delivery.md:46` / `:448` mention Git in prose; the scan flags them until reworded, which is intended.
- The prohibition sentence itself ("runs git or gh") does not match the scan because no repository verb follows.
- If `moai update` regenerates the managed files, AC-GITOWN-001 to -004 and -007 to -010 fail against the regenerated copies; AC-GITOWN-013 records that, and the override rule (AC-GITOWN-005) is the part expected to persist.

## Quality Gate and Definition of Done

- AC-GITOWN-001 to -010 and -012 pass with recorded output; AC-GITOWN-011 passes or is reported as a Gap with the reason; AC-GITOWN-013 is recorded.
- The RED baselines of AC-GITOWN-002 and -004 are recorded before the first edit.
- No file outside the 14-file edited set changes; `AGENTS.md` is byte-identical to `<base_sha>` (`git diff`), and `spec-workflow.md` and the other protected files match the recorded sha256 values.
- plan-auditor PASS threshold for Tier M: 0.80.
