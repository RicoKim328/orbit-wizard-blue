---
description: "Sync Phase 13~14 — Git Operations and Delivery (CI mirror, push/PR, auto-merge), Completion, Graceful Exit, Test Scenarios, and Custom Harness."
user-invocable: false
metadata:
  parent: moai-workflow-sync
  phase: "Phase 13~14: Git Delivery, Completion, and Auxiliary"
---

<!-- TRACE PROBE: workflow-split baseline trace mechanism -->
<!-- Activated by MOAI_TRACE_PHASES=1 environment variable -->
<!-- Emits one line per Phase entry/exit to stderr in format: [trace] /moai sync Phase <N> <enter|exit> -->

### Phase 13: Git Operations and Delivery

#### Step 3.0: Detect Git Workflow Strategy

Read `github.spec_git_workflow` from `.moai/config/sections/system.yaml`. This determines how changes are delivered.

| Strategy | Branch Model | PR Behavior | Best For |
|----------|-------------|-------------|----------|
| github_flow | Feature branches off main | Auto-create PR to main | Team/OSS projects |
| main_direct | Direct commits to main | No PR created | Solo development |
| gitflow | develop/release/hotfix branches | PR to appropriate base | Enterprise projects |

Default strategy (if not configured): `github_flow`

The same `github.spec_git_workflow` key also determines SPEC branch handling:
- `feature_branch`: Each SPEC gets its own branch (recommended for github_flow/gitflow)
- `main_direct`: SPEC changes committed to current branch (only when spec_git_workflow is main_direct)

#### Step 3.1: Commit Changes

**Tier-based Route gate** (per `.claude/rules/moai/workflow/spec-workflow.md` § SPEC Phase Discipline): read the SPEC's `tier` field (S/M/L) and whether `--pr` was passed.

Only the orchestrator runs git or gh (`.claude/rules/project/git-ownership.md`). In both routes the agent returns the single sync commit as a proposed repository action and the orchestrator executes it.

- **Route A (Tier S/M default, no `--pr`)**: Agent: manager-docs subagent. manager-docs returns the single sync commit as a proposed repository action targeting `main`; the orchestrator executes it — no feature branch, no PR.
- **Route B (Tier L OR explicit `--pr`)**: Agent: manager-docs subagent, with `manager-git` (proposal-only) drafting the branch name and commit message when requested. The same single sync commit is returned as a proposed repository action targeting the sync feature branch (`sync/SPEC-XXX` or `chore/SPEC-XXX-sync`); the orchestrator executes it and delivers it via PR in Step 3.2.

Both routes — the proposed repository action contains:
- The file list to stage: all changed document files, reports, README, docs/
- A single commit with descriptive message listing synchronized documents, project repairs, and SPEC updates
- Commit message language following the `language.git_commit_messages` setting
- The exact commands, which the orchestrator runs and then confirms the resulting commit:

Proposed repository action — single sync commit (the orchestrator executes it):
```bash
git add <listed document, report, README, and docs/ paths>
git commit -m "<sync commit subject>" -m "<sync commit body per Step 3.1.1>"
```

#### Step 3.1.1: Context Memory Generation in Git Commits

Purpose: Embed structured context within the sync commit message carried by the proposed repository action, to enable seamless session resumption across development cycles.

**Context Collection Process:**

1. **Decision Tracking**: Gather all decisions made during the sync phase
   - Documentation choices and rationale
   - SPEC update approach and divergence handling
   - Project improvement selections
   - Quality trade-offs accepted or deferred

2. **Constraint Discovery**: Record any constraints identified
   - Formatting requirements discovered
   - API documentation standards applied
   - Platform-specific considerations
   - Technology limitations encountered

3. **Gotcha Documentation**: Note issues found during documentation review
   - Outdated references in existing documentation
   - Missing API documentation sections
   - Inconsistencies between code and docs
   - Breaking changes requiring user notification

4. **Pattern Usage**: Document patterns applied during sync
   - Documentation templates used
   - Code-to-doc mapping strategies
   - Mermaid diagram patterns for architecture
   - README.md structure improvements

**Commit Format for Sync Phase:**

All sync commits MUST include structured context using this format:

```
docs(sync): [brief description of changes]

## SPEC Reference
SPEC: SPEC-XXX
Phase: SYNC
Timestamp: ISO-8601 timestamp

## Context (AI-Developer Memory)
- Decision: [documentation decision 1]
- Decision: [documentation decision 2]
- Pattern: [pattern 1 applied]
- Pattern: [pattern 2 applied]
- Constraint: [constraint discovered]
- Gotcha: [issue found and how resolved]

## Affected Areas
- Documents Updated: [count]
- SPEC Status: [completed|in-progress]
- Coverage Impact: [change or percentage]
```

#### Step 3.1.5: Local CI Mirror Validation (Pre-PR Gate)

Purpose: Replicate CI checks locally before pushing and creating a PR to catch failures fast, without waiting for slow remote CI. Windows-specific tests are skipped (cannot run locally).

**Trigger condition**: Only run when a PR is about to be created (github_flow feature branch, gitflow feature/release/hotfix). Skip for `main_direct` strategy and direct pushes to main/develop.

##### Step 3.1.5.1: Discover CI Configuration

Read `.github/workflows/` to auto-detect CI jobs:
- If `ci.yml` (or any CI file) exists: parse jobs, steps, and commands
- If no CI config found: skip this phase entirely, log "No CI config detected"

Build a local execution plan mapping each CI job to its local equivalent:

| CI Job | CI Runner | Local Equivalent | Skippable |
|--------|-----------|-----------------|-----------|
| test (ubuntu) | ubuntu-latest | Local OS tests | No (run on current OS) |
| test (macos) | macos-latest | Local OS tests | No (identical on macOS) |
| test (windows) | windows-latest | **SKIP** | Yes — cannot run locally |
| lint | ubuntu-latest | Local lint | No |
| build (cross-compile) | ubuntu-latest | Local cross-compile | No |

##### Step 3.1.5.2: Run Local Equivalents in Parallel

**Go project** (detected via `go.mod`):

Launch all checks in parallel:

```bash
# Check 1: go vet (mirrors CI step)
go vet ./...

# Check 2: Tests with race detector (mirrors CI test job)
go test -race -coverprofile=coverage.out -covermode=atomic ./...

# Check 3: golangci-lint (mirrors CI lint job)
# Auto-detect if golangci-lint is available
which golangci-lint && golangci-lint run --timeout=5m \
  || echo "SKIP: golangci-lint not installed (install via your project's pinned version)"

# Check 4: Cross-compile all CI targets (mirrors CI build job)
# Replace <your-module> with your main package path (e.g. ./cmd/<your-binary>/).
# Replicate whatever GOOS/GOARCH targets your CI build matrix declares; the
# example below shows the common 5-target matrix — run them in parallel, CGO_ENABLED=0 for all.
GOOS=linux   GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s -w" -o /tmp/ci-build-linux-amd64     ./<your-module>/ &
GOOS=linux   GOARCH=arm64 CGO_ENABLED=0 go build -ldflags="-s -w" -o /tmp/ci-build-linux-arm64     ./<your-module>/ &
GOOS=darwin  GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s -w" -o /tmp/ci-build-darwin-amd64    ./<your-module>/ &
GOOS=darwin  GOARCH=arm64 CGO_ENABLED=0 go build -ldflags="-s -w" -o /tmp/ci-build-darwin-arm64    ./<your-module>/ &
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s -w" -o /tmp/ci-build-windows-amd64.exe ./<your-module>/ &
wait
```

**Python project** (detected via `pyproject.toml`):

```bash
pytest --tb=short
ruff check . && ruff format --check .
mypy . --ignore-missing-imports
```

**TypeScript/JavaScript project** (detected via `package.json`):

```bash
npm test -- --run
npm run lint
npm run build
```

**Other languages**: Run the standard test + lint + build commands discovered from CI config.

**Cross-platform build targets**: If CI config shows `strategy.matrix` with multiple `os` or `GOOS/GOARCH` values, replicate all cross-compile targets using the local toolchain.

##### Step 3.1.5.3: Skipped Checks Report

Always report what was skipped and why:

```
CI Mirror: Skipped checks
- test (windows-latest): Cannot run Windows tests locally — will be verified by remote CI
- lint: golangci-lint not installed — install via your project's pinned version
```

##### Step 3.1.5.4: Evaluate Results

**All checks pass**: Proceed to Step 3.2 automatically. Log "Local CI mirror: PASS".

**Any check fails**: Present failure summary via AskUserQuestion:

- Fix now — delegate to manager-develop subagent with failure details, then re-run CI mirror
- Push anyway — proceed to Step 3.2 with warning embedded in PR description
- Abort — exit sync workflow, preserve commit (allow local fix and re-run)

**golangci-lint not installed**: Treat as warning (not failure). Proceed to Step 3.2 with a note in the PR description: "Local lint check skipped: golangci-lint not installed."

##### Step 3.1.5.5: Embed Results in PR Description

Pass CI mirror results to Step 3.2 for inclusion in the PR body:

```markdown
## Local CI Mirror Results
| Check | Status | Notes |
|-------|--------|-------|
| go vet | ✅ Pass | |
| go test -race (macOS) | ✅ Pass | Coverage: 87% |
| golangci-lint | ✅ Pass | |
| build linux/amd64 | ✅ Pass | |
| build linux/arm64 | ✅ Pass | |
| build darwin/amd64 | ✅ Pass | |
| build darwin/arm64 | ✅ Pass | |
| build windows/amd64 | ✅ Pass | |
| test (windows) | ⏭ Skipped | Cannot run locally |
```

#### Step 3.2: Push and Deliver (Strategy-Aware)

Behavior varies based on `github.spec_git_workflow` setting and current branch context.

Every push, PR, and merge step below is a proposed repository action: the agent returns it (`manager-git`, proposal-only, may draft the PR title and body) and the orchestrator executes it. The orchestrator also supplies the current branch and any PR state the steps depend on. The Route A / Route B tier policy from Step 3.1 is unchanged.

**Base Branch Resolution** (applies to all strategies below):
1. Read `git_strategy.mode` from `.moai/config/sections/git-strategy.yaml`
2. Resolve `main_branch`:
   - If `git_strategy.{mode}.main_branch` exists: use that value
   - If missing (e.g., `manual` mode): default to `main`
3. Use `{main_branch}` in all branch checkout and PR creation commands below

##### Strategy: github_flow

Detect current branch:

**Feature branch** (any branch other than main):
1. Push the branch to the remote
2. Check whether a PR already exists for the branch
3. If no PR exists: create the PR
   - Title: Derived from SPEC title or branch name
   - Body: Include sync summary, files changed, quality report, deployment readiness notes (migrations, env changes, breaking changes)
   - If SPEC metadata contains `issue_number` (non-zero): Include `Fixes #{issue_number}` in PR body footer for automatic Issue closure on merge
   - Base: {main_branch}
   - Labels: auto-detected from changed files
4. If PR exists: Update with comment summarizing sync changes
5. Display PR URL to user

Proposed repository action — github_flow feature branch (the orchestrator executes it):
```bash
git push -u origin <branch>
gh pr list --head <branch> --json number
# only when no PR exists:
gh pr create --base {main_branch} --title "<title>" --body "<body>" --label "<labels>"
# only when a PR exists:
gh pr comment <number> --body "<sync summary>"
```

**Main branch** (direct commit):
- Push directly (proposed repository action below)
- Display push confirmation
- Note: Direct main commits are the Route A default for Tier S/M SPECs; feature branches apply to Route B (Tier L or explicit `--pr`)

Proposed repository action — github_flow main branch (the orchestrator executes it):
```bash
git push origin {main_branch}
```

**Worktree context** (detected from the repository directory structure the orchestrator reports):
- Same proposed repository action as the feature branch flow, for the worktree branch
- Display PR URL and worktree context

##### Strategy: main_direct

All commits go directly to main, no PRs:
1. Push to main (proposed repository action below)
2. Display push confirmation
3. No PR created regardless of branch name

Proposed repository action — main_direct (the orchestrator executes it):
```bash
git push origin main
```

##### Strategy: gitflow

Detect current branch type and route accordingly. Each branch type below is one proposed repository action that the orchestrator executes:

**feature/* branch** → PR to `develop`:
1. Push the branch
2. Create or update PR targeting `develop` branch
3. Display PR URL

**release/* branch** → PR to `main`:
1. Push the branch
2. Create or update PR targeting `main` branch
3. Display PR URL

**hotfix/* branch** → PR to `main` (and back-merge to develop):
1. Push the branch
2. Create or update PR targeting `main` branch
3. After merge: Create follow-up PR to `develop` for back-merge
4. Display PR URLs

Proposed repository action — gitflow feature/release/hotfix branch (the orchestrator executes it; `<base>` is `develop` for feature, `main` for release and hotfix):
```bash
git push -u origin <branch>
gh pr create --base <base> --title "<title>" --body "<body>"
# hotfix only, after merge:
gh pr create --base develop --head <branch> --title "<back-merge title>" --body "<body>"
```

**develop branch** → Push directly:
1. Push to develop (proposed repository action below)
2. Display push confirmation

Proposed repository action — gitflow develop branch (the orchestrator executes it):
```bash
git push origin develop
```

**main branch** → Error:
- Direct commits to main are not allowed in gitflow
- Suggest creating a hotfix or release branch instead

#### Step 3.3: PR Ready Transition (Team Mode)

Only applies when a PR was created in Step 3.2:

- If Team mode enabled and PR is draft: transition it to ready, and assign reviewers and labels if configured, as a proposed repository action the orchestrator executes
- If Team mode disabled: Do NOT automatically transition (user controls readiness)

Proposed repository action — PR ready transition (the orchestrator executes it):
```bash
gh pr ready <number>
gh pr edit <number> --add-reviewer "<reviewers>" --add-label "<labels>"
```

#### Step 3.3.5: Return to Base Branch (Post-PR Cleanup)

After PR/MR creation (Step 3.2) and optional ready transition (Step 3.3), return to the base branch to leave the working directory in a clean state. The return is a proposed repository action the orchestrator executes:

**github_flow**: switch to `{main_branch}` and pull it
**gitflow**: switch to `develop` and pull it (for feature branches), or switch to `main` and pull it (for release/hotfix)
**main_direct**: No branch switch needed (already on main)

Proposed repository action — return to base branch (the orchestrator executes it; `<base>` is `{main_branch}` for github_flow, `develop` or `main` for gitflow):
```bash
git checkout <base> && git pull origin <base>
```

This ensures the developer's working directory is on the base branch, ready for the next task. The feature branch remains on the remote for review.

Remote branch cleanup after merge is handled by the hosting platform's auto-delete setting (GitHub: "Automatically delete head branches", GitLab: "Delete source branch when merge request is accepted", Bitbucket: "Close source branch"). Local branch deletion is left to the developer.

#### Step 3.4: Auto-Merge Behavior

Only applies when a PR was created in Step 3.2.

##### Auto-Merge Trigger Conditions

Auto-merge trigger conditions:
- `is_worktree_context == true` AND `--no-merge` flag NOT set
- OR `--merge` flag explicitly set (deprecated, logged as warning)

When auto-merge is triggered (each check and the merge are part of the proposed repository action in Auto-Merge Execution below, which the orchestrator executes):
1. Verify all CI/CD checks pass
2. Verify zero merge conflicts
3. If all checks pass: squash-merge the PR and delete its branch
4. If checks fail: Report error with recovery command, do NOT merge

##### Flag Behavior

- `--no-merge`: Skip auto-merge even in worktree context. PR is created but not merged.
- `--merge`: Deprecated. Logs warning: "The --merge flag is deprecated. Auto-merge is now the default for worktree contexts."

##### Auto-Merge Execution

1. Check CI/CD status (wait for completion)
2. Check merge conflicts
3. If passing and mergeable: squash-merge and delete the branch
4. Check out the target branch, fetch latest
5. Verify local is synchronized with remote

Proposed repository action — auto-merge (the orchestrator executes it, stopping at the first failed check):
```bash
gh pr checks <number> --watch
gh pr view <number> --json mergeable
gh pr merge <number> --squash --delete-branch
git checkout <target> && git fetch origin
git rev-list --count --left-right origin/<target>...HEAD
```

##### Auto-Merge Failures

- If CI/CD fails: Report failure, display error details, do NOT merge
- If merge conflicts: Report conflicts, provide manual resolution guidance, do NOT merge
- If approvals missing (Team mode): Report pending approvals, do NOT merge

##### Post-Merge Automatic Cleanup

Condition: Auto-merge succeeded AND `workflow.worktree.auto_cleanup == true`

Steps:
1. Detect worktree path for current SPEC-ID from registry
2. The orchestrator executes cleanup equivalent to `moai worktree done SPEC-{ID} --auto --delete-branch` (a proposed repository action when drafted by an agent):
   - Remove worktree directory
   - Remove feature branch (already deleted by --delete-branch in merge)
   - Update worktree registry
3. Log cleanup result

Error handling:
- Cleanup failure does NOT block or affect merge result
- On failure: Log warning with manual cleanup command
- Message: "Worktree cleanup warning: {error}. Manual: `moai worktree done SPEC-{ID}`"

### Phase 14: Completion and Next Steps

#### Completion Report

Display summary including:
- Git workflow strategy used (github_flow, main_direct, or gitflow)
- Sync mode and scope
- Files updated and created
- Project improvements made
- Documents updated
- Reports generated
- Backup location
- PR URL (if created) or push target (if direct push)

#### Context-Aware Next Steps

Full-pipeline completion close: when this sync phase completed as the tail of a `full-pipeline` contract AND no genuine pending decision remains, close with the Completion Report as a clean completion statement — NO manufactured next-step question is emitted (the askuser-protocol § Completion-Report Next-Step Discipline "close with NO question" clause is the full-pipeline default). A genuine next-step decision, when one actually exists, still rides AskUserQuestion. The option lists below apply to `single-phase` contract completions (explicit `/moai sync` invocation), whose "(Recommended)" next-step chain question is unchanged.

Tool: AskUserQuestion with options tailored to delivery result (single-phase contract):

**If PR was created (github_flow feature branch, or gitflow):**
- Review PR on GitHub (Recommended)
- Auto-Merge PR (/moai sync --merge)
- Create Next SPEC (/moai plan)
- Start New Session (/clear)

**If direct push (main_direct, or github_flow main branch):**
- Create Next SPEC (/moai plan) (Recommended)
- Continue Development
- Start New Session (/clear)

**If worktree context:**
- Review PR in Browser (Recommended)
- Return to Main Directory
- Remove This Worktree

---

## Graceful Exit

When user aborts at any decision point:

- No changes made to documents, Git history, or branch state
- Project remains in current state
- Display retry command: /moai sync [mode]
- Exit with code 0

---

## Completion Criteria

All of the following must be verified:

- Phase 1: Deployment readiness verified (tests, migrations, env changes, backward compatibility)
- Phase 7: Quality verification completed (tests, linter, type checker, deep code review with auto-fix)
- Phase 8: Security scan completed (if security-sensitive files changed)
- Phase 10: Coverage analysis completed (measurement, gap analysis, test generation, verification)
- Phase 11: Prerequisites verified, project analyzed, divergence analysis completed, sync plan approved by user
- Phase 12: Safety backup created and verified, documents synchronized, SPEC documents updated per lifecycle level, project documents updated (if applicable), quality verified, SPEC status updated
- Phase 13: Changes committed, local CI mirror validated (Step 3.1.5: vet + test-race + lint + cross-compile — Windows skipped), delivered per spec_git_workflow strategy (PR created for github_flow/gitflow, direct push for main_direct), auto-merge executed (if flagged and PR exists)
- Phase 14: Completion report displayed with delivery result, appropriate next steps presented based on strategy and context

---

## Test Scenarios

### Normal Flow
**Prompt**: "/moai sync SPEC-AUTH-001"
**Expected Result**:
- Phase 1: Pre-sync quality gate passes (tests, lint)
- Phase 7: Quality verification confirms TRUST 5 compliance
- Phase 11: Divergence analysis shows implementation matches SPEC
- Decision Point: User approves sync plan
- Phase 12: Documentation updated (README, CHANGELOG, API docs)
- Phase 12: SPEC status updated to "implemented"
- Phase 13: Commits created, PR opened with summary

### Partial Implementation Flow
**Prompt**: "/moai sync SPEC-AUTH-001" (only backend implemented, frontend pending)
**Expected Result**:
- Phase 11: Divergence detected - 3/5 acceptance criteria met
- Sync plan notes partial implementation
- SPEC status updated to "in-progress" (not "implemented")
- Documentation reflects completed portions only
- PR description notes remaining work

### Error Flow
**Prompt**: "/moai sync" (no SPEC specified, uncommitted changes exist)
**Expected Result**:
- Auto-detect: Finds uncommitted changes on current branch
- AskUserQuestion: "Sync changes on current branch?"
- If user confirms, syncs based on the uncommitted changes the orchestrator reports
- If no changes found, reports "Nothing to sync"

---

Version: 4.0.0
Changes: Added test scenarios (3.7.0) + Related Skills section (3.8.0) + removed the Related Skills CI watch/auto-fix routing entry (4.0.0 — the CI watch loop is not part of the distributed toolchain).

---

## Custom Harness Extension (Optional)

@.moai/harness/sync-extension.md

*(이 파일은 `/moai project --harness`로 생성됩니다. 파일이 없으면 자동으로 skip됩니다.)*
