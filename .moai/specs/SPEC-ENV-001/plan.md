# SPEC-ENV-001 — Implementation Plan (Tier S)

## §A Context

Remove the literal `PATH` from the shared `env` block, make the repository itself ignore `.claude/settings.local.json`, and track exactly those two files (`.claude/settings.json`, `.gitignore`). Direction decided by the user: project-local hardening plus upstream issue https://github.com/modu-ai/moai-adk/issues/1827 as the root-cause tracker. User decisions applied in iteration 2: track only the files this SPEC modifies; the status-line home path belongs to SPEC-HOOKS-001.

## §B Known Issues / Evidence Base

Read by the author on 2026-10-18:

- `.claude/settings.json:339-356` (statusLine, env), `:118-157` and `:170` (Stop and SubagentStop hook registrations), `.claude/settings.local.json` (whole file), `.gitignore` of the primary checkout and this worktree, `/home/rico/.config/git/ignore`, `/home/rico/.bashrc:118,121`, `/home/rico/.profile:19-37`, `handle-codex-review-gate.sh:62-74`, `handle-multi-review-gate.sh:66-82`, `chain-event.sh:10-23`.
- Session probe: `printenv PATH` equals the eight-entry literal; `MOAI_CONFIG_SOURCE=sections`; `command -v ruff` exit 1; `.venv/bin/ruff` exists; `command -v node` is `/usr/bin/node` v12.22.9 and the Codex plugin script fails on it, while the nvm Node v24.19.0 runs it.
- `moai update --help`: "synchronize embedded templates with the project"; `--shell-env` "Configure shell environment variables for Claude Code"; `--templates-only`, `--no-hooks`, `--yes`. `strings` on the binary shows a "settings.json / status_line.sh merge-preserved" label in a clean-reinstall path (context not read). These are leads for the measurements below, not conclusions.

## §C Pre-flight and run-phase measurement tasks

1. Record `base_sha` (taken immediately before this SPEC's first run edit; run phases are executed one at a time) and save `$SCRATCH/settings.before.json` (a copy of `.claude/settings.json` before any edit) in `progress.md` §E.2; `export SCRATCH`, `export REPO`; record the `protected_sha256:` block defined in `spec.md` §3 Conventions.
2. **Obtain `$LAUNCH_PATH` from the user** (the coordinator session is daemon-spawned and cannot observe it): the coordinator asks the user to run `printenv PATH` in a normal interactive terminal and paste the result; record it verbatim with the provenance `user-supplied`. Then run AC-ENV-002. A negative result is a blocker report to the orchestrator and the `PATH` entry stays; a missing `$LAUNCH_PATH` makes AC-ENV-002, -004, and -005 Gaps.
3. **Replace versus merge.** Run the baseline probe of AC-ENV-004 (original `settings.json`, explicit `env PATH="$REPO/.venv/bin:$LAUNCH_PATH"`): the first printed entry discriminates replace (`/home/rico/.local/bin`) from merge (`$REPO/.venv/bin`); record the word in `progress.md` §E.2.
4. **Origin of the entry and `moai update` behavior** (AC-ENV-008): run the always-real scratch update on both the original and the changed `settings.json` with an isolated `HOME`, record `cmp`, whether `PATH` appears, and any user-level state created.
5. **Does `$PATH` expand inside `env` values?** Only needed if a local override is wanted that appends rather than replaces: probe with a throwaway project whose `.claude/settings.local.json` sets `env.ENV001_EXPAND` to `"x:${PATH}"` and read the value from a Bash-tool call. Record the result; no repo file depends on it.
6. Record the expected review-gate noise: until the dependency SPECs land, the MoAI Codex gate (`workflow.yaml:63`) reviews uncommitted tooling changes at each Stop; the runtime caps consecutive Stop blocks at 8 (`hooks-system.md:213-215`). Expected, not a defect of this SPEC.

## §D Constraints

- JSON edit only: delete line 355 and the trailing comma on line 354; no reformatting of other lines.
- `.gitignore`: add one entry, `.claude/settings.local.json`; do not reorder or remove existing lines.
- Do not copy author-specific values into any tracked file.
- Do not edit any hook wrapper (the `$HOME/.local/bin` question is answered by the AC-ENV-002 precondition instead).
- Sub-agents run no `git`/`gh`; the coordinator runs every command in `spec.md` §3.
- `development_mode: tdd`: AC-ENV-001, -003 and -006 are run first against the unmodified files (RED: `True` becomes `False`, `exit=1` becomes `exit=0`) and again after the edit.

## §E Self-Verification

Run AC-ENV-001 to AC-ENV-008 in §F order (coordinator), recording each command with its verbatim output in `progress.md` §E.2. AC-ENV-004, -005 need fresh Claude Code sessions; AC-ENV-008 is a measurement. Unavailable or negative results are Gaps, never PASS from reading.

## §F Tasks (ordered by decision-reversibility, most likely to change first)

1. **Confirm the precondition (§C step 2).** If AC-ENV-002 fails, stop and report.
2. **Edit `.claude/settings.json`.** Remove the `PATH` entry (line 355) and the trailing comma on line 354. Run AC-ENV-001 and AC-ENV-003.
3. **Edit `.gitignore`.** Add `.claude/settings.local.json`. Run AC-ENV-006.
4. **Probe the effective environment.** Run AC-ENV-004 and AC-ENV-005 in fresh sessions from a venv-activated shell.
5. **Measure `moai update`.** Run AC-ENV-008; carry any negative result to the orchestrator.
6. **Commit (coordinator).** Stage `.claude/settings.json` and `.gitignore` by explicit pathspec. Run AC-ENV-007.
7. **Sync-phase follow-up (manager-docs).** If `.moai/project/tech.md` documents the Claude settings, note that PATH is inherited and where local overrides live.

### Files to modify

| File | Line | Change |
|---|---|---|
| `.claude/settings.json` | 354-355 | remove `"PATH": ...`; drop the comma after `"CLAUDE_CODE_NO_FLICKER": "1"` |
| `.gitignore` | end | add `.claude/settings.local.json` |

## Risks

| ID | Risk | Evidence / Mitigation |
|---|---|---|
| R1 | Removing the override breaks `moai` resolution for the three wrappers with no `$HOME/.local/bin` tier (`handle-codex-review-gate.sh`, `handle-multi-review-gate.sh`, `chain-event.sh`) when the launching shell lacks it. | E4; the AC-ENV-002 precondition blocks the removal in that case. |
| R2 | After removal, `node` for such sessions changes from v12.22.9 to v24.19.0 (nvm sourced after the PATH exports in `~/.bashrc`), so the Codex plugin's `node` hooks start running for real. | Expected and desirable; noted so the first Stop after the change is not mistaken for a regression. AC-ENV-004 records the `node` path. |
| R3 | `moai update` re-injects `PATH` or overwrites the tracked file. | AC-ENV-008 measures it. |
| R4 | Tracking the whole `.claude/settings.json` publishes permissions and hook paths. | The plan-audit scanned the file: no secrets. The user decided to track the file this SPEC modifies. |
| R5 | The probe depends on how Claude Code is launched; a venv activated in a different shell than the launcher proves nothing. | AC-ENV-004/-005 state the launch condition; record `$LAUNCH_PATH`. |
| R6 | A tracked `.gitignore` entry does not untrack an already tracked file. | `settings.local.json` is untracked today; AC-ENV-006 checks ignore state only. |

## §G Anti-Patterns

- Do not copy the removed PATH literal into any tracked file.
- Do not hand-edit other keys while editing the file.
- Do not report AC-ENV-004/-005 as PASS from the authoring-session probe; that probe is the baseline.
- Do not edit the wrappers or `.moai/status_line.sh` here.
- Do not `git add -A`.

## MX Tag Plan

None. No source file with `@MX` annotations is touched.

## §H Cross-References

- `.claude/settings.json:339-356`, `.claude/hooks/moai/handle-codex-review-gate.sh:62-74`, `.claude/hooks/moai/handle-multi-review-gate.sh:66-82`, `.claude/hooks/moai/chain-event.sh:10-23`, `.claude/hooks/moai/handle-pre-tool.sh:71-81`.
- SPEC-HOOKS-001 (status-line path ownership, D5), SPEC-REVGATE-001 (depends on this SPEC), SPEC-GITOWN-001.

## Deferred (no decision needed to start)

- Adding a `$HOME/.local/bin` tier to the three wrappers: not needed while AC-ENV-002 holds; a follow-up if a developer's launching shell lacks `moai` on PATH.

## Open decisions for Kickoff Approval

None.
