---
id: SPEC-REVGATE-001
title: "Define blocking versus advisory behavior and finding acknowledgement for the MoAI Codex stop-time review gate"
version: "0.3.0"
status: draft
created: 2026-10-18
updated: 2026-10-18
author: Rico
priority: P2
phase: "v0.1.1 target"
module: ".claude/hooks/moai/handle-codex-review-gate.sh"
lifecycle: spec-anchored
tags: "codex, review-gate, stop-hook, advisory, acknowledgement, tooling, hardening"
tier: S
depends_on: [SPEC-HOOKS-001, SPEC-ENV-001, SPEC-GITOWN-001]
---

# SPEC-REVGATE-001: Define blocking versus advisory behavior and finding acknowledgement for the MoAI Codex stop-time review gate

## HISTORY

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1.0 | 2026-10-18 | Rico | Initial draft (Tier S) |
| 0.2.0 | 2026-10-18 | Rico | Iteration 2 (plan-audit findings X-1..X-5, X-7..X-9, R-1..R-10) |
| 0.3.0 | 2026-10-18 | Rico | Iteration 3 (re-audit R2-1..R2-8, C-1..C-3): the gate output shape is now observed (`observed-gate-output.md`), so the shape-conditional requirements and the Shape T/N branches are removed; register keyed on normalized title + path with six fields, seeded from the observed text with evidence that survives the dependency SPECs; stub cases for the no-verdict limbs; sha256 records replace `git diff` checks on untracked files; contiguous `base_sha`; defined scratch copy |

## 1. Context

According to the coordinator, an automated Codex review gate ran at the end of repeated turns on 2026-10-18 and repeated largely the same findings about the untracked MoAI tooling files each time, with slightly different finding sets per run, while the application showed 169 passed tests and a clean Ruff run. The author did not see the gate's output; the coordinator captured two of the messages verbatim in `observed-gate-output.md` (this directory; five such messages were observed in total, each with a different finding set and wording). That file is the evidence base for the output shape and for the register seeds. Upstream tracker: https://github.com/modu-ai/moai-adk/issues/1827 (open; it lists the exec, PATH, TSV, trap, and Git-ownership items and describes the review gate only as the source of the findings, read through a WebFetch summary). Resolution direction (user decisions): project-local hardening, tracked in git, in parallel with the upstream tracker; the MoAI gate is kept (`workflow.yaml:63`) with a register of acknowledged findings; the Codex plugin gate stays as it is (disabled).

All line numbers below were read on 2026-10-18 in `/home/rico/Desktop/Project/orbit-wizard-blue` (untracked MoAI tooling) and in the installed Codex plugin.

### G1 — Two separate Codex stop-time gates exist
- **MoAI gate (kept).** Wrapper `.claude/hooks/moai/handle-codex-review-gate.sh` (85 lines, read in full), registered in the Stop array at `.claude/settings.json:144-149` through the absence-tolerant `bash -c` wrapper (a missing script is logged to `.moai/logs/hook-missing.log` and exits 0), `timeout: 900`. It exits 0 at once unless `.moai/config/sections/workflow.yaml` has `workflow.codex.review_gate.enabled: true` (`:35-60`). In this repository it is `true` (`workflow.yaml:61-63`; confirmed by loading the YAML with the project's PyYAML), although the comment at `:56-60` says it ships OFF. It then resolves `moai` through `$CLAUDE_PROJECT_DIR/../../moai`, `PATH`, and `$HOME/go/bin/moai` (`:62-74`) and pipes the Stop payload to `moai hook codex-review-gate`, always exiting 0 (`:82-85`); fail-open when `moai` is missing (`:78-80`). `moai hook codex-review-gate` is described in the binary as running "the codex JSON-RPC reviewer against uncommitted changes" and emitting the standard ALLOW/BLOCK Stop-hook output, "Opt-in via workflow.codex.review_gate.enabled (default off). Fail-open: any error logs to stderr and exits 0" (seen with `strings`; the Go handler source was not available). The wrapper header says the handler blocks "on a fail verdict" (`:9-12`).
- **Codex plugin gate (stays disabled; not changed).** Plugin `codex@openai-codex` v1.0.6 is enabled at `~/.claude/settings.json:7`; its `hooks/hooks.json` registers `scripts/stop-review-gate-hook.mjs` for Stop (`timeout: 900`). It acts only when the workspace's `stopReviewGate` is true (`stop-review-gate-hook.mjs:154-157`), toggled with `/codex:setup --enable-review-gate|--disable-review-gate` (`codex-companion.mjs:79,221-234`), default `false` (`lib/state.mjs:23`). Read by the author with a modern Node (`node scripts/codex-companion.mjs setup --json`, from the primary checkout and from this worktree): `reviewGateEnabled` is `False` in both. It also blocks when the review times out, fails, returns empty output, or answers unexpectedly (`:69-96,112-139`). Under the authoring session's overridden PATH, `node` resolves to v12.22.9 and the plugin script fails with `SyntaxError: Unexpected token '?'`.
- The observed messages carry the prefix `codex review gate:` (`observed-gate-output.md`), not the plugin gate's block text (which begins "Codex stop-time review found issues that still need fixes before ending the session:", `stop-review-gate-hook.mjs:87`), and the coordinator names the hook as `handle-codex-review-gate.sh`; the MoAI gate is therefore the source.

### G2 — The configuration knobs that exist (verified by reading)
1. `workflow.codex.review_gate.enabled` in `.moai/config/sections/workflow.yaml:63`, the only field of the Go configuration struct for the MoAI gate (seen with `strings`).
2. The Stop registration at `.claude/settings.json:144-149` (removing it, or deleting the wrapper script, disables the MoAI gate; the registration `timeout` is `900`).
3. The plugin's per-workspace `stopReviewGate` toggle (`/codex:setup --enable-review-gate` / `--disable-review-gate`; read-only status via `node scripts/codex-companion.mjs setup --json`, field `reviewGateEnabled`).
4. Plugin enablement (`enabledPlugins` in `~/.claude/settings.json`).
5. The wrapper header says the Go handler self-gates to ALLOW on a no-edit, loop-prevention, or disabled turn (`:9-12`); how is unverified. The Claude Code runtime also caps consecutive Stop-hook blocks at 8, tunable with `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` (`.claude/rules/moai/core/hooks-system.md:213-215`).
6. `mcp__moai__codex_setup` appears in the `super-advisor.md` tool list; its schema was not read, so its effect is unverified and it is not used here.

There is no severity threshold, no path exclusion, and no acknowledgement or waiver list in either gate as read. The register of this SPEC is a new, project-local file read only by the wrapper.

### G3 — The observed output shape (from `observed-gate-output.md`)
- A message is the prefix `codex review gate: `, a one-paragraph summary, a line `Full review comments:`, then bullets of the form `- [P#] <title> — <absolute path>:<line or line-range>` followed by an indented body (two spaces). Severity `[P2]` on every item seen. Title and location are separated by ` — ` (em dash).
- Finding sets differ between runs, and the same defect recurs under different titles and shifted line ranges (for example the status-line defect: "Allow the status-line temporary-file cleanup to run" in one run and "Allow status-line cleanup to run after MoAI exits" in another, ranges `22-24` both times; the navigator defect `251-251` then `251-252`). Therefore a finding is identified by its normalized title plus its path, never by its line range, and a reworded title is a new finding (it blocks; the register then needs one more entry).
- Not observed: the JSON envelope of the handler's stdout (only the displayed text was captured). AC-REVGATE-003 step 0 records it once at run time and fails if the text shape differs from the above.

### G4 — Why findings repeat, and what the register can and cannot do (hypothesis, not tested)
- The MoAI handler reviews uncommitted changes. The untracked tooling files stay uncommitted until the dependency SPECs land, so each stop re-reviews them, and the gate does not remember a finding it has already reported.
- The observed defects are exactly those the dependency SPECs fix. With those SPECs completed first (hard `depends_on`), every observed title is a `fixed-in` entry, which never suppresses; the active (suppressing) population of the register is empty by construction at seed time. The register therefore does not shorten the interim repetition; it is the mechanism for findings triaged later (`upstream-tracked`, `accepted`), and its `fixed-in` entries make a returning fixed defect recognizable. The interim repetition ends when the dependency fixes are committed (G3 hypothesis).

### G5 — Interactions
- SPEC-ENV-001: once the PATH override is removed, the wrapper finds `moai` through the launching shell's PATH (AC-ENV-002 there is the precondition).
- SPEC-HOOKS-001 D4: whether a Stop-hook block must be top-level applies to any gate that emits one; AC-REVGATE-003 step 0 records the handler's actual envelope.

## 2. Requirements (GEARS)

### REQ-REVGATE-001 — One active gate
While the MoAI Codex stop-time review gate is enabled for a workspace (`workflow.codex.review_gate.enabled: true`), the Codex plugin stop-time review gate (`stopReviewGate`) shall be disabled for that workspace.

### REQ-REVGATE-002 — Disposition policy is documented
The repository shall contain one tracked document, `.moai/project/review-gate-policy.md`, that states, for the MoAI gate, when it blocks a stop, when it is advisory only, how a stop is allowed past it, and which configuration knobs exist, each knob cited with the file and line (or command) that defines it, user-level files cited as `~/...`.

### REQ-REVGATE-003 — Acknowledged findings do not re-block
Where the MoAI gate is enabled, when the handler's block lists findings in the observed format and every finding is matched by an active register entry, the gate wrapper shall allow the stop and shall show those findings as non-blocking advisory text. A finding is matched when its normalized title (lower case, whitespace collapsed, trailing punctuation removed) equals the entry's title and its path, with the project root prefix and the `:lines` suffix removed, equals the entry's path; line ranges are ignored.

### REQ-REVGATE-004 — Register content and seeds
Each line of the acknowledged-findings register `.moai/project/review-gate-acks.tsv` shall have six non-empty tab-separated fields (title, project-relative path, disposition in `fixed-in`/`upstream-tracked`/`accepted`, tracker reference, date, evidence), and the file shall contain no header or comment lines. Only `upstream-tracked` and `accepted` entries are active. The seeded entries shall be one per distinct title in `observed-gate-output.md`, each with the evidence field naming the sample and item it was copied from, and the trackers shall include SPEC-HOOKS-001, SPEC-ENV-001, SPEC-GITOWN-001, and https://github.com/modu-ai/moai-adk/issues/1827.

### REQ-REVGATE-005 — A missing verdict does not make the wrapper block
Where the MoAI gate is enabled, when the handler writes nothing to stdout, exits non-zero (including a timeout-style status), or writes output that is not a block, the wrapper shall exit 0 and shall add no block decision of its own; when `moai` is not resolvable it shall exit 0 with empty output.

### REQ-REVGATE-006 — Exactly the gate files are tracked
The repository shall track exactly the wrapper `.claude/hooks/moai/handle-codex-review-gate.sh`, the policy document, and the register for this change.

### REQ-REVGATE-007 — Inactive and unmatched findings do not suppress
Where the MoAI gate is enabled, when a block contains at least one finding matched by no active register entry (including a finding matched only by a `fixed-in` entry), or when the register is missing or has a malformed line, the wrapper shall leave the handler's output byte-identical.

### REQ-REVGATE-008 — Scope preservation
The change shall not modify the `moai` binary, the Codex plugin, `workflow.yaml` or any other `.moai/config` file, `AGENTS.md`, any file under `src/`, `tests/`, `tools/`, `packaging/`, or `.github/`, any hook other than `handle-codex-review-gate.sh`, or any other tracked file.

## 3. Acceptance Criteria (inline, Tier S)

Conventions.
- `$REPO` is the checkout holding the gate files. `$SCRATCH` is a new empty directory outside any git repository (`export SCRATCH`). `<base_sha>` is `git rev-parse HEAD` taken immediately before this SPEC's first run edit; the four tooling SPECs' run phases are executed one at a time, in the order HOOKS, ENV, GITOWN, REVGATE, so each name-only diff lists only this SPEC's files. `$NODE` is a Node.js that can run the Codex plugin and `$CODEX_COMPANION` is `scripts/codex-companion.mjs` under the installed plugin directory; both paths are recorded in `progress.md` §E.2 (bare `node` on a PATH overridden per SPEC-ENV-001 can be v12 and fail).
- Verification roles: the coordinator (orchestrator) runs every command in this section and records the verbatim output in `progress.md` §E.2; implementers only edit files and report. ACs marked **[coordinator-run]** call `git`, run `moai` or codex, or open a live Claude Code session; sub-agents run none of them.
- Protected-file record (replaces `git diff` on untracked paths, which cannot fail): at the first run edit the coordinator records in `progress.md` §E.2, in `sha256sum` format under `protected_sha256:`, the hashes of `.moai/config/sections/*.yaml`, of every `.claude/hooks/moai/*.sh` except the wrapper, of every file under the installed Codex plugin directory, and of the `moai` binary; at the end it writes those lines to `$SCRATCH/protected.sha256` and runs `sha256sum -c "$SCRATCH/protected.sha256"`.
- Scratch copy for `moai update`: `mkdir -p "$SCRATCH/updcopy" && tar -C "$REPO" --exclude=.git --exclude=.venv -cf - . | tar -C "$SCRATCH/updcopy" -xf -`, then `(cd "$SCRATCH/updcopy" && find . -type f | sort > "$SCRATCH/before.txt")`.
- Fixture G (gate scratch): a git repository `$SCRATCH/gate` (created by the coordinator) with one commit and an uncommitted file, `.moai/config/sections/workflow.yaml` containing nested `workflow:` / `codex:` / `review_gate:` / `enabled: true`, and `$SCRATCH/bin/moai`, a stub that prints the envelope recorded in step 0 of AC-REVGATE-003 around a block text in the observed format with two findings: X (`- [P2] Title X one — $SCRATCH/gate/p/x.sh:10-12`) and Y (`- [P2] Title Y two — $SCRATCH/gate/p/y.sh:20-21`), each with an indented body. `ACK` denotes the register at `$SCRATCH/gate/.moai/project/review-gate-acks.tsv`.

### AC-REVGATE-001 — The plugin gate is disabled while the MoAI gate is enabled (REQ-REVGATE-001) [coordinator-run]
- Given the change is applied and `progress.md` §E.2 lists every workspace root the coordinator uses (the primary checkout, this worktree, and the coordinator's own worktree)
- When, for each listed root `$W`, `"$REPO/.venv/bin/python" -c "import yaml; print(yaml.safe_load(open('$W/.moai/config/sections/workflow.yaml'))['workflow']['codex']['review_gate']['enabled'])"` and, from `$W`, `"$NODE" "$CODEX_COMPANION" setup --json | python3 -c "import json,sys; print(json.load(sys.stdin)['reviewGateEnabled'])"` are run (a root without `workflow.yaml` is skipped and recorded)
- Then wherever the first prints `True`, the second prints `False`

### AC-REVGATE-002 — Policy document exists and its knobs check out (REQ-REVGATE-002) [coordinator-run]
- Given the change is applied
- When `git ls-files --error-unmatch .moai/project/review-gate-policy.md` is run, then `grep -c -E '^## (When the gate blocks|When the gate is advisory|Allowing a stop past the gate|Configuration knobs)$' .moai/project/review-gate-policy.md` is run
- Then the first prints the path and exits 0, and the second prints `4`
- And for each knob listed under "Configuration knobs", its cited `file:line` exists and `sed -n '<line>p' <file>` contains the knob's key; the per-knob results are recorded in `progress.md` §E.2
- And `grep -n -E '/home/[^ ]+' .moai/project/review-gate-policy.md; echo "exit=$?"` prints only `exit=1`

### AC-REVGATE-003 — Acknowledged findings pass; others are untouched (REQ-REVGATE-003, REQ-REVGATE-007) [coordinator-run]
Step 0 (re-confirm the observed shape once, at run time): run the real wrapper once in a scratch git repository with the gate enabled and an uncommitted change containing one obvious defect; save the verbatim raw stdout in `progress.md` §E.2 and record the envelope (which JSON key holds the block decision and which holds the reason text). Pass condition: the reason text begins `codex review gate:`, contains a line `Full review comments:`, and contains at least one line matching `^- \[P[0-9]\] .+ — .+:[0-9]+(-[0-9]+)?$`. If the shape differs, this AC and REQ-REVGATE-003 fail and the run phase stops with a blocker report requesting an amendment; no other shape is specified.

In every following run: `printf '{"session_id":"s1"}' | PATH="$SCRATCH/bin:/usr/bin:/bin" CLAUDE_PROJECT_DIR="$SCRATCH/gate" bash "$REPO/.claude/hooks/moai/handle-codex-review-gate.sh" > "$SCRATCH/out.txt"; echo "exit=$?"` prints `exit=0`; `"$SCRATCH/bin/moai" hook codex-review-gate > "$SCRATCH/raw.txt"` is the reference output; "blocks" means `out.txt` carries the block decision recorded in step 0.
- Given ACK with an `upstream-tracked` entry for X (title `title x one`, path `p/x.sh`) and an `accepted` entry for Y; Then `out.txt` does not block and contains the text of both findings as advisory text
- And with the same entries but X reported as `p/x.sh:99-120` (stub variant with a shifted range), `out.txt` does not block (line ranges are ignored)
- And with only the X entry, `cmp "$SCRATCH/out.txt" "$SCRATCH/raw.txt"` reports identical (the block stands, byte-identical)
- And with an empty ACK, a missing ACK, an ACK with one malformed line (five fields), or both entries `fixed-in`, `cmp` reports identical
- And with both entries active but Y reported under a reworded title, `cmp` reports identical (a reworded title is a new finding)
- And with X and Y both active and a third bullet that does not match the observed shape (for example `- [P1] No location given`), `cmp` reports identical (an unparsed bullet is never ignored)
- And with X and Y both active and a block that contains no bullets at all, `cmp` reports identical (zero parsed bullets is never treated as "all acknowledged")

### AC-REVGATE-004 — Register entries are well-formed and traceable to the observed text (REQ-REVGATE-004) [coordinator-run]
- Given the change is applied
- When `awk -F'\t' 'NF!=6 || $1=="" || $2=="" || $3!~/^(fixed-in|upstream-tracked|accepted)$/ || $4=="" || $5!~/^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$/ || $6=="" {print FILENAME ":" FNR}' .moai/project/review-gate-acks.tsv` is run
- Then it prints nothing (this also rejects header and comment lines)
- And the register has exactly one entry per distinct title in `observed-gate-output.md` (10 at seed time: 5 in sample A, 5 in sample B)
- And for each entry, the sample item named in its evidence field has a normalized title equal to the entry's title and a path that ends with the entry's path; the per-entry results are recorded in `progress.md` §E.2
- And `grep -c -F 'SPEC-HOOKS-001'`, `'SPEC-ENV-001'`, `'SPEC-GITOWN-001'`, and `'https://github.com/modu-ai/moai-adk/issues/1827'` on the register each print at least `1`

### AC-REVGATE-005 — A missing verdict does not make the wrapper block (REQ-REVGATE-005) [coordinator-run]
- Given fixture G with ACK empty
- When the AC-REVGATE-003 wrapper command is run with the stub replaced by (a) a stub printing nothing and exiting 0, (b) a stub printing nothing and exiting 124 (timeout-style), (c) a stub printing `not json` and exiting 0
- Then in every case it prints `exit=0` and `out.txt` carries no block decision (for (a) and (b) `out.txt` is empty)
- And with `PATH="/usr/bin:/bin"` and an empty `HOME="$SCRATCH/home"` (no `moai` resolvable), it prints `exit=0` and `out.txt` is empty
- And with `$SCRATCH/onlymoai/` containing only a symlink `moai` to the real binary's absolute path, `PATH="$SCRATCH/onlymoai:/usr/bin:/bin" command -v codex; echo "exit=$?"` prints only `exit=1`, and the wrapper run with that PATH in a git scratch repo prints `exit=0` with no block decision in `out.txt`
- If the real `moai` binary cannot be run in the scratch repository, the last bullet is reported as a Gap, not a pass.

### AC-REVGATE-006 — A real new finding still blocks (REQ-REVGATE-003, REQ-REVGATE-007) [coordinator-run]
- Given a scratch git repository with an uncommitted change that contains a deliberate, obvious defect, the gate enabled, and an empty register
- When a Claude Code session in that repository ends a turn after making that change
- Then the session is blocked from stopping with the reviewer's finding; recorded in `progress.md` §E.2
- If no live session or reviewer run is available, the criterion is reported as a Gap, not a pass.

### AC-REVGATE-007 — Exactly three files are tracked and changed; protected files unchanged (REQ-REVGATE-006, REQ-REVGATE-008) [coordinator-run]
- Given the run-phase commit exists
- When `git ls-files --error-unmatch .claude/hooks/moai/handle-codex-review-gate.sh .moai/project/review-gate-policy.md .moai/project/review-gate-acks.tsv; git status --porcelain -- .claude/hooks/moai/handle-codex-review-gate.sh .moai/project/review-gate-policy.md .moai/project/review-gate-acks.tsv` is run
- Then the three paths are printed and the status output is empty
- And `git diff --name-only <base_sha>..HEAD -- . ':(exclude).moai/specs'` prints exactly those three paths
- And `git diff --name-only <base_sha>..HEAD -- src tests tools packaging .github AGENTS.md` prints nothing
- And `sha256sum -c "$SCRATCH/protected.sha256"` reports `OK` for every recorded file (`workflow.yaml` and the other `.moai/config` files, the other hooks, the plugin files, and the `moai` binary are unchanged)

### AC-REVGATE-008 — `moai update` treatment is measured (supports REQ-REVGATE-006) [coordinator-run]
- Given the scratch copy defined in Conventions, an empty `$SCRATCH/updhome`, and `moai update --help` output saved in `progress.md` §E.2
- When `cd "$SCRATCH/updcopy" && HOME="$SCRATCH/updhome" moai update --templates-only --no-hooks --yes` is run (always the real run in the scratch copy), followed by `cmp` of each of the three files against its `$REPO` version, `find . -type f | sort` diffed against `$SCRATCH/before.txt`, and `ls -R "$SCRATCH/updhome"`
- Then `progress.md` §E.2 holds the verbatim output, one line per file `<path>: preserved` or `<path>: overwritten-or-merged` (with the diff), the list of files the update created or changed, and any user-level state created
- If the wrapper differs, the filter is not durable against `moai update`; this is reported as a Gap with the restoring step. The policy document and register are not template files and are expected to persist.

## 4. Exclusions

### Out of Scope — The reviewers themselves
- No change to the `moai` binary, its Go handler, the Codex plugin or its prompt, `workflow.yaml`, or the reviewer's model and effort.
- No change to what the reviewer decides is a finding; the SPEC governs only what the wrapper does with the verdict.

### Out of Scope — The dependency fixes
- The hook, PATH, and Git-ownership defects are fixed in SPEC-HOOKS-001, SPEC-ENV-001, and SPEC-GITOWN-001; this SPEC does not fix them and only references them in the register.

### Out of Scope — The multi-model gate, other Stop hooks, and other output shapes
- No change to the multi-model review gate (`handle-multi-review-gate.sh`, `workflow.multi.review_gate`), `handle-stop-goal.sh`, `sync-phase-quality-gate.sh`, or the security hooks.
- No handling of any handler output shape other than the observed one, no fuzzy title matching, and no expiry or automatic removal of register entries.

### Out of Scope — Upstream
- No edit of upstream issue #1827 and no upstream patch; asking upstream for a native acknowledgement option is a separate decision.
