# SPEC-REVGATE-001 — Implementation Plan (Tier S)

## §A Context

Keep the MoAI Codex stop-time review gate, and make already-triaged and upstream-tracked findings stop re-blocking through a register read by the wrapper, while a new or returning finding still blocks. Wrapper change plus two new project files (policy document, register); no change to the reviewer, the plugin, or `workflow.yaml`. Direction decided by the user: project-local hardening plus upstream issue https://github.com/modu-ai/moai-adk/issues/1827 as the root-cause tracker. This SPEC depends on SPEC-HOOKS-001, SPEC-ENV-001, and SPEC-GITOWN-001 (`depends_on`): all three must be `completed` before run-phase entry.

User decisions applied: (1) track only the files this SPEC modifies (wrapper, policy document, register); (4) keep the MoAI gate (`workflow.yaml:63`) and add a register; the Codex plugin gate stays as it is (disabled) and is not changed. Locations chosen by the author: policy document `.moai/project/review-gate-policy.md`, register `.moai/project/review-gate-acks.tsv` (six tab-separated non-empty fields, no header or comment lines, parsed with `awk -F'\t'`), both under the already-tracked `.moai/project/` tree.

Iteration 3: the handler's output shape is observed (`observed-gate-output.md`, captured by the coordinator): `codex review gate: <summary>`, `Full review comments:`, bullets `- [P#] <title> — <path>:<lines>` with an indented body. The requirements are written for that shape only. A finding's identity is its normalized title plus its path; line ranges drift and are ignored; the same defect recurs under reworded titles, so each wording needs its own entry (a reworded title blocks, the safe direction). Expectation set honestly: with the dependency SPECs completed first, every seeded entry is `fixed-in` (never suppresses), so the active population is empty at seed time (`spec.md` §1 G4).

## §B Known Issues / Evidence Base

Read by the author on 2026-10-18:

- `.claude/hooks/moai/handle-codex-review-gate.sh` (whole file), `.claude/settings.json:118-157`, `.moai/config/sections/workflow.yaml:56-72`, `.claude/rules/moai/core/hooks-system.md:211-222`.
- Codex plugin v1.0.6: `hooks/hooks.json`, `scripts/stop-review-gate-hook.mjs`, `prompts/stop-review-gate.md` (whole files), `scripts/codex-companion.mjs:79,185-250`, `scripts/lib/state.mjs:9-52`.
- Binary `strings`: the Go configuration struct for the codex gate has only `Enabled`; the `moai hook codex-review-gate` help text; `templates/.claude/hooks/moai/handle-codex-review-gate.sh` is embedded.
- Runtime reads: YAML load of `workflow.yaml` gives `workflow.codex.review_gate.enabled = True`; plugin `reviewGateEnabled = False` in the primary checkout and in this worktree.
- Coordinator-captured, verbatim: `observed-gate-output.md` (samples A and B; titles, paths, and ranges used for the register seeds).
- Plan-time source snapshot (the lines the reviewer cited, copied from the primary checkout on 2026-10-18) is recorded in `progress.md` §E.1, so register evidence does not depend on those lines surviving the dependency SPECs.
- Not verified: the Go handler's source and JSON envelope, how it detects a no-edit turn, `moai update` behavior, the coordinator's own worktree plugin state.

## §C Pre-flight and run-phase measurement tasks

1. Confirm SPEC-HOOKS-001, SPEC-ENV-001, and SPEC-GITOWN-001 are `completed`; if not, do not start (`depends_on` is a hard dependency).
2. Record `base_sha` (taken immediately before this SPEC's first run edit; run phases are executed one at a time) in `progress.md` §E.2; `export SCRATCH`, `export REPO`; record the `$NODE` and `$CODEX_COMPANION` paths and the list of workspace roots the coordinator uses. Record the `protected_sha256:` block defined in `spec.md` §3 Conventions.
3. **Re-confirm the shape once (AC-REVGATE-003 step 0, coordinator-run).** Run the real wrapper in a scratch git repository with the gate enabled and one obvious defect uncommitted; save the verbatim raw stdout and the envelope (which key holds the decision and which the reason) in `progress.md` §E.2. If the text shape differs from the observed one, stop and report; the SPEC's AC fails.
4. Measure `moai update` (AC-REVGATE-008): build the scratch copy as defined in Conventions, save `moai update --help`, run the always-real scratch update with an isolated `HOME`, record per-file `cmp`, the created/changed file list, and any user-level state created.
5. Record the expected noise: the MoAI gate reviews uncommitted changes at every Stop, and this SPEC itself leaves uncommitted files; the runtime caps consecutive Stop blocks at 8 (`hooks-system.md:213-215`).

## §D Constraints

- Pure shell in the wrapper; no `jq`, as the wrapper header requires (`handle-codex-review-gate.sh:30-31`); the register is parsed with `awk -F'\t'` (never `read` with a tab IFS, see SPEC-HOOKS-001 D3).
- Keep the OFF fast path: with the gate disabled the wrapper exits 0 before any binary resolution (`:35-60`).
- Keep fail-open: a missing `moai` or an unavailable reviewer never blocks (`:76-80`, handler help text); the wrapper adds no block decision of its own.
- Never hide a finding: acknowledged findings are shown as advisory text, not dropped.
- Only `upstream-tracked` and `accepted` entries suppress; `fixed-in` entries never do; any non-suppressed case leaves the handler's output byte-identical.
- Normalization: lower-case, collapse whitespace, strip trailing punctuation from the title; strip the project root prefix and the `:lines` suffix from the path.
- Sub-agents run no `git`/`gh`/`moai`/codex; the coordinator runs every command in `spec.md` §3. The register records references, never secrets.
- `development_mode: tdd`: the stub-based fixtures of AC-REVGATE-003 and -005 are the tests; write them first and watch them fail against the unmodified wrapper.

## §E Self-Verification

Run AC-REVGATE-001 to AC-REVGATE-008 in §F order (coordinator), recording each command with its verbatim output in `progress.md` §E.2. AC-REVGATE-005 (real-binary bullet), -006 and -008 are Gaps until their live runs exist.

Non-gating observation: after the dependency SPECs and this SPEC land, note the gate's disposition at the end of three consecutive turns (informational; there is no requirement behind it).

## §F Tasks (ordered by decision-reversibility, most likely to change first)

1. **Run §C step 3** and fix the envelope-dependent details: where the reason text sits in the handler's stdout and how advisory text is emitted (`systemMessage` for a Stop hook).
2. **Write the failing fixtures first** (AC-REVGATE-003, -005): a stub `moai` printing the recorded envelope around the observed format with two findings.
3. **Write the policy document** with the four headings AC-REVGATE-002 checks; cite the knobs of `spec.md` §1 G2 with `file:line`, user-level files as `~/...`.
4. **Implement the filter in the wrapper.** After the handler call (`:82`), parse the findings (`- [P#] <title> — <path>:<lines>` bullets), normalize title and path, and compare with the active register entries; if every finding is matched, print the findings as advisory text and no block; in every other case (any unmatched finding, `fixed-in`-only match, missing or malformed register, unparseable output) print the handler's output unchanged.
5. **Seed the register** with one entry per distinct title in `observed-gate-output.md` (10 entries, all `fixed-in`): see the seed table below; the evidence field names the sample and item.
6. **Run the real-binary checks** (AC-REVGATE-005 last bullet, AC-REVGATE-006).
7. **Commit (coordinator)** by explicit pathspec (wrapper, policy document, register); run AC-REVGATE-007 and -008.

### Register seeds (from `observed-gate-output.md`)

| Title (as printed) | Path (project-relative) | Tracker | Evidence |
|---|---|---|---|
| Keep Git operations with Astra | `.claude/agents/moai/manager-git.md` | SPEC-GITOWN-001, issue #1827 | sample A, item 1 |
| Exit after invoking the resolved goal-hook binary | `.claude/hooks/moai/handle-stop-goal.sh` | SPEC-HOOKS-001, issue #1827 | sample A, item 2 |
| Remove the machine-specific shared PATH override | `.claude/settings.json` | SPEC-ENV-001, issue #1827 | sample A, item 3 |
| Preserve empty columns when reading navigator rows | `.claude/skills/moai-workflow-project/scripts/navigator-regen.sh` | SPEC-HOOKS-001, issue #1827 | sample A, item 4 |
| Allow the status-line temporary-file cleanup to run | `.moai/status_line.sh` | SPEC-HOOKS-001, issue #1827 | sample A, item 5 |
| Exit after dispatching the goal hook | `.claude/hooks/moai/handle-stop-goal.sh` | SPEC-HOOKS-001, issue #1827 | sample B, item 1 |
| Emit the Stop decision at the top level | `.claude/hooks/moai/sync-phase-quality-gate.sh` | SPEC-HOOKS-001 | sample B, item 2 |
| Run Ruff from the project virtual environment | `.claude/hooks/moai/sync-phase-quality-gate.sh` | SPEC-HOOKS-001 | sample B, item 3 |
| Preserve empty fields when reading navigator rows | `.claude/skills/moai-workflow-project/scripts/navigator-regen.sh` | SPEC-HOOKS-001, issue #1827 | sample B, item 4 |
| Allow status-line cleanup to run after MoAI exits | `.moai/status_line.sh` | SPEC-HOOKS-001, issue #1827 | sample B, item 5 |

All ten are `fixed-in` dated with the sync date; a tracker field with two references uses a `+` separator without spaces (for example `SPEC-HOOKS-001+https://github.com/modu-ai/moai-adk/issues/1827`).

### Files to modify

| File | Change |
|---|---|
| `.claude/hooks/moai/handle-codex-review-gate.sh` | register post-filter after the handler call |
| `.moai/project/review-gate-policy.md` (new) | disposition policy and knob list |
| `.moai/project/review-gate-acks.tsv` (new) | acknowledged-findings register |

## Risks

| ID | Risk | Evidence / Mitigation |
|---|---|---|
| R1 | The handler's JSON envelope differs from what the stub assumes. | §C step 3 records the real envelope and AC-REVGATE-003 step 0 fails the SPEC if the text shape differs. |
| R2 | A broad match hides a real regression. | Identity is exact normalized title plus path; `fixed-in` entries never suppress; acknowledged findings are always shown. |
| R3 | A future change enables the plugin gate as well, doubling reviews and blocks. | REQ-REVGATE-001 and AC-REVGATE-001. |
| R4 | `moai update` overwrites the wrapper from its embedded template. | AC-REVGATE-008 records it; recovery is the tracked copy; the policy document and register are not template files. |
| R5 | The runtime's 8-block cap (`hooks-system.md:213-215`) ends a repeat loop without a verdict. | Informational; the dependency fixes, not the cap, end the repetition. |
| R6 | Reworded titles for the same defect each need an entry. | Accepted: a reworded title blocks (safe direction); entries are cheap. |
| R7 | Stale `upstream-tracked` entries outlive their tracker issue. | No expiry in this SPEC (Exclusions); entries carry a date and a tracker. |

## §G Anti-Patterns

- Do not drop or rewrite the reviewer's finding text; show it.
- Do not invent configuration keys; the only gate key is `workflow.codex.review_gate.enabled`.
- Do not make an acknowledgement mean "always allow"; a single unmatched finding must still block, and a returning `fixed-in` finding must block.
- Do not key a finding on its line range.
- Do not seed register entries from text not in `observed-gate-output.md`.
- Do not report AC-REVGATE-003 step 0 or AC-REVGATE-006 as PASS from the stub alone.
- Do not `git add -A`; stage by pathspec.

## MX Tag Plan

None. No source file with `@MX` annotations is touched.

## §H Cross-References

- `.claude/hooks/moai/handle-codex-review-gate.sh:9-85`, `.moai/config/sections/workflow.yaml:56-72`, `.claude/settings.json:144-149`, `.claude/rules/moai/core/hooks-system.md:211-222`.
- `observed-gate-output.md` (this directory); Codex plugin `scripts/stop-review-gate-hook.mjs:154-176` (read-only reference).
- SPEC-HOOKS-001 (D4 block channel), SPEC-ENV-001 (PATH, `moai` resolution), SPEC-GITOWN-001.

## Deferred (no decision needed to start)

- Expiry of acknowledgements when a tracker closes: not in this SPEC.
- A native acknowledgement or advisory option from modu-ai/moai-adk: separate upstream request.
- `mcp__moai__codex_setup` (schema not read): not used.
- Fuzzy matching of reworded titles: not in this SPEC.

## Open decisions for Kickoff Approval

None.
