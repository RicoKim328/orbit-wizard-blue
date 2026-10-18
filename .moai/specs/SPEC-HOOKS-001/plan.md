# SPEC-HOOKS-001 — Implementation Plan (Tier S)

## §A Context

Fix five reported defects (D1-D5, evidence in `spec.md` §1) in four MoAI-managed shell files and track exactly those four files in git. Tooling-only change; no Python source is touched. Direction decided by the user: project-local hardening plus upstream issue https://github.com/modu-ai/moai-adk/issues/1827 as the root-cause tracker. User decisions applied in iteration 2: track only the files this SPEC modifies (the four below); the hard-coded user path in `.moai/status_line.sh` is owned here.

## §B Known Issues / Evidence Base

Read by the author on 2026-10-18 (primary checkout `/home/rico/Desktop/Project/orbit-wizard-blue`):

- `handle-stop-goal.sh:64-79`, `handle-pre-tool.sh:16-21,60-81`, `.moai/status_line.sh:1-44`, `navigator-regen.sh:143-182,242-262`, `sync-phase-quality-gate.sh:1-409`, `.claude/rules/moai/core/hooks-system.md:100-110,388`, `.claude/rules/moai/development/hook-independence.md` (always-exit-0 wrapper doctrine), `.claude/settings.json:118-157,339-356`.
- Reproduction status per defect: D1 mechanism only (isolated replica); D2 reproduced on the real file; D3 mechanism only; D4 not reproduced (documentation corroborates the Codex claim); D5 skip path by reading, lint command run by hand.
- Local patch for D5 exists in the primary checkout (`diff` against `/home/rico/.claude/jobs/fadbe668/tmp/sync-phase-quality-gate.sh.bak` differs only at lines 230-240). The backup is a job-tmp file and the only copy of the original; C3 copies it into the evidence in `progress.md` §E.2.
- `moai update --help`: "synchronize embedded templates with the project"; flags `--templates-only`, `--no-hooks` (git-hook installation), `--dry-run`, `--force`, `--yes`. The binary embeds `templates/.claude/hooks/moai/*`.

## §C Pre-flight and run-phase measurement tasks

1. Record `base_sha` (`git rev-parse HEAD`, coordinator, taken immediately before this SPEC's first run edit; run phases are executed one at a time in the order HOOKS, ENV, GITOWN, REVGATE) in `progress.md` §E.2; set `$REPO`; `export SCRATCH` to a fresh directory outside any git repository; record the `protected_sha256:` block defined in `spec.md` §3 Conventions.
2. Record the RED baseline: run AC-HOOKS-001, -002, -003 and -004 against the unmodified files; they are expected to FAIL (several calls and the wrong exit status for D1, a leaked file and the home-path branch for D2, a shifted row for D3, a nested block for D4). A fixture that passes before the fix is a broken fixture.
3. Copy the D5 backup file's relevant lines (the original python branch) and the `diff` against the current gate into `progress.md` §E.2, and confirm the diff still differs only in the python branch.
4. Measure `moai update` (AC-HOOKS-007): save `moai update --help`, run the always-real scratch update with an isolated `HOME`, record per-file `cmp` results and any user-level state created. This replaces the former "does update preserve local edits" question.
5. Measure Stop-block enforcement on Claude Code 2.1.302 (AC-HOOKS-008) before editing `sync-phase-quality-gate.sh:391-399`; the edit itself is pinned to the top-level form by the documentation and does not wait for the result, but a negative result is escalated to the orchestrator.
6. Record the expected review-gate noise: until the dependency SPECs land, the MoAI Codex gate (`workflow.yaml:63`) reviews the uncommitted tooling changes at each Stop; the runtime's block cap is 8 consecutive Stop blocks (`hooks-system.md:213-215`). This is expected, not a defect of this SPEC.

## §D Constraints

- Shell-only change to four files. No new dependency; no `jq` (hook-independence doctrine, `handle-stop-goal.sh:46-50`).
- Keep the goal-less fast path of `handle-stop-goal.sh` (`:55-59`) behaviorally identical: zero `moai` cold starts.
- The stop-goal wrapper contract is fixed: dispatch once, then `exit 0` in every branch (fail-open, as `hook-independence.md` and `handle-stop-goal.sh:78-79` have it). The evaluator's exit status is not passed through; stderr keeps going to `$MOAI_HOOK_STDERR_LOG`.
- Keep exit-0 semantics of the sync-phase gate (`:405-409`).
- Sub-agents run no `git`/`gh`; the coordinator runs every command in `spec.md` §3.
- `development_mode: tdd`: the AC fixtures are the tests; RED first (§C step 2), then GREEN.

## §E Self-Verification

Run AC-HOOKS-001 to AC-HOOKS-008 in §F order (coordinator), recording each command with its verbatim output in `progress.md` §E.2. AC-HOOKS-007 and AC-HOOKS-008 are measurements: a failing or unavailable result is a Gap, never a PASS from reading.

Non-gating observation: after the run-phase commit, note whether the leaked-file count in `/tmp` stops growing (informational; the cleanup of existing files is out of scope).

## §F Tasks (ordered by decision-reversibility, most likely to change first)

1. **Apply the D4 decision.** In `sync-phase-quality-gate.sh` emit the top-level form `{"decision":"block","reason":...,"systemMessage":...}` at `:393-394`; keep advisory at `:396-397`; rewrite only the comments that assert the nested form (`:377-383` and `:387`). The header lines `:15` and `:35` already document the top-level form and stay. Run AC-HOOKS-004.
2. **Choose the ruff directory selection (REQ-HOOKS-006).** In the python branch (`:228-241`) build the argument list from the existing directories among `src tests tools` (else `.`), for both the venv ruff and the `PATH` fallback. Run AC-HOOKS-005.
3. **Fix D1.** In `handle-stop-goal.sh` replace each `printf ... | exec ...` with a plain pipeline followed by `exit 0` in each tier, following the structure of `handle-pre-tool.sh:66-81` but with the always-exit-0 contract. Keep the stderr redirect. Run AC-HOOKS-001.
4. **Fix D3.** In `navigator-regen.sh` make the progress-map loop (`:251-260`) parse tab-separated rows without collapsing empty fields (for example render that table with `awk -F'\t'` as `:212` and `:237` do, or read with a non-whitespace separator). Keep output byte-identical for rows with all fields present. Run AC-HOOKS-003.
5. **Fix D2 and the path.** In `.moai/status_line.sh` replace each `exec <moai> statusline < "$temp_file"` with an invocation followed by `exit $?`; delete the absolute-path branch at `:29-31` (the `$HOME`-relative branches remain) and the comment at `:26-28` that describes it ("Try the installed binary's own resolved path ..."). Run AC-HOOKS-002.
6. **Commit (coordinator).** One run-phase commit naming SPEC-HOOKS-001, staging exactly the four files by pathspec. Run AC-HOOKS-006.
7. **Measurements.** Run AC-HOOKS-007 and AC-HOOKS-008 and record the results; carry any negative result to the orchestrator before sync.
8. **Sync-phase follow-up (manager-docs).** If `.moai/project/structure.md` lists tooling, note that these four files are tracked.

### Files to modify

| File | Lines | Change |
|---|---|---|
| `.claude/hooks/moai/sync-phase-quality-gate.sh` | 228-241, 377-383, 387, 391-399 | directory-selected ruff; top-level Stop block; comment correction |
| `.claude/hooks/moai/handle-stop-goal.sh` | 64-66, 69-71, 74-76 | single dispatch, `exit 0` per tier |
| `.claude/skills/moai-workflow-project/scripts/navigator-regen.sh` | 251-260 | parse that preserves empty fields |
| `.moai/status_line.sh` | 23, 26-31, 35, 40 | no `exec`, exit with the binary's status; remove the user-path branch |

## Risks

| ID | Risk | Evidence / Mitigation |
|---|---|---|
| R1 | `moai update` regenerates the files from embedded templates and discards the fix. | Embedded templates seen in the binary; AC-HOOKS-007 measures it; recovery is the tracked version. |
| R2 | The D4 fix makes a block enforceable that was effectively never enforced; with D5 live a ruff failure at a sync commit will hard-block turn-end (once per commit: the sentinel is written before the checks, `:178-186`). | Intended behavior; documented here; `MOAI_SYNC_GATE_BLOCKING=0` and `MOAI_AUTONOMY_TIER` remain the opt-outs. |
| R3 | A project missing one of `src`/`tests`/`tools` would block on ruff E902. | REQ-HOOKS-006 and AC-HOOKS-005 (missing directories). |
| R4 | AC fixtures need `HOME`/`PATH` overrides and a scratch git repo; some sandboxes refuse them. | The coordinator runs them from a normal shell; any refused step is a Gap. |
| R5 | While the dependency SPECs are open, the MoAI Codex gate re-reviews the uncommitted tooling changes at each Stop and the 8-block cap may end a loop without a verdict. | §C step 6; SPEC-REVGATE-001 handles the repetition class. |
| R6 | The `$HOME/.local/bin` tier of the stop-goal and status-line wrappers is now the only route to a `~/.local/bin` install when PATH lacks it. | Both wrappers keep that tier (`handle-stop-goal.sh:74-76`, `status_line.sh:39-41`). |

## §G Anti-Patterns

- Do not use `exec` inside a pipeline, or anywhere an EXIT trap must run.
- Do not edit `handle-pre-tool.sh`; it is the reference, not a target.
- Do not pass the evaluator's exit status out of the stop-goal wrapper.
- Do not report AC-HOOKS-001..005 as PASS without a fresh run of the exact commands, and do not treat the isolated replica from the authoring session as a pass.
- Do not `git add -A`; stage by pathspec.
- Do not delete the leaked `/tmp` files as part of this change.

## MX Tag Plan

None. Shell files carry no `@MX` tags and no Python source changes.

## §H Cross-References

- `.claude/hooks/moai/handle-pre-tool.sh:16-21,60-81`, `.claude/rules/moai/core/hooks-system.md:100-110,213-215,388`, `.claude/rules/moai/development/hook-independence.md`, `.claude/settings.json:118-157,339-343`.
- SPEC-ENV-001 (PATH override; references the status-line path as owned here), SPEC-GITOWN-001, SPEC-REVGATE-001.

## Deferred (no decision needed to start)

- Making a skipped gate check visible in the gate log (today a skip logs `ruff=0`, the same as a pass): not changed here; a follow-up SPEC if wanted.
- Reporting D4 and D5 upstream: separate decision, not part of this SPEC.

## Open decisions for Kickoff Approval

None.
