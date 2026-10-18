---
id: SPEC-HOOKS-001
title: "Harden MoAI hook and script defects reported by the Codex review gate"
version: "0.3.0"
status: draft
created: 2026-10-18
updated: 2026-10-18
author: Rico
priority: P1
phase: "v0.1.1 target"
module: ".claude/hooks/moai"
lifecycle: spec-anchored
tags: "hooks, shell, stop-hook, statusline, navigator, ruff, codex-review, tooling, hardening"
tier: S
---

# SPEC-HOOKS-001: Harden MoAI hook and script defects reported by the Codex review gate

## HISTORY

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1.0 | 2026-10-18 | Rico | Initial draft (Tier S) |
| 0.2.0 | 2026-10-18 | Rico | Iteration 2 (plan-audit findings X-1..X-5, X-7..X-9, H-1..H-11): single tracking scope; wrapper contract fixed; Stop block pinned to top level; ruff directory selection; status-line path owned here; always-real `moai update` measurement; coordinator-run marking |
| 0.3.0 | 2026-10-18 | Rico | Iteration 3 (re-audit H2-1..H2-4, C-1..C-3): `env -u` placement fixed in AC-HOOKS-004; sha256 record replaces the unverifiable "other hooks unchanged" claim; contiguous `base_sha`; defined scratch copy; stale status-line comment added to the edit list |

## 1. Context

Five defects in MoAI-managed shell tooling were reported by the automated Codex review gate, as relayed by the coordinator. The files are untracked in the primary checkout (`/home/rico/Desktop/Project/orbit-wizard-blue`) and absent from this worktree. Resolution direction (user decision): project-local hardening, tracked in git so the fix is reviewable, in parallel with the upstream root-cause tracker https://github.com/modu-ai/moai-adk/issues/1827. That issue (open, opened 2026-10-17, moai-adk 3.1.2; read through a WebFetch summary) covers D1, D2 and D3 below; it does not mention D4 or D5.

All line numbers were read from the files on 2026-10-18.

### D1 — Stop-goal wrapper can run the evaluator more than once
- Location: `.claude/hooks/moai/handle-stop-goal.sh:64-66` (PATH tier), `:69-71` (`$HOME/go/bin`), `:74-76` (`$HOME/.local/bin`), final `exit 0` at `:79`.
- Observed by reading: each tier is `printf '%s' "$INPUT" | exec <moai> hook stop-goal 2>>"$MOAI_HOOK_STDERR_LOG"` inside an `if`. `exec` in a pipeline element replaces only that pipeline's subshell, so the parent shell continues into the later tiers and ends at `exit 0`. With an armed goal and `moai` resolvable at more than one tier the evaluator runs once per tier and can emit more than one JSON decision for one Stop event. The same directory holds the correct pattern: `handle-pre-tool.sh:66-81` runs the pipeline without `exec` and then `exit`s in every tier, and its header comment (`:16-21`) documents this exact hazard. A grep over `.claude/hooks/moai/*.sh` (plan-audit) found no other `| exec`.
- Reproduced by author: partial. An isolated replica of the three-tier control flow (stub binaries in a scratch dir; not the real wrapper) printed three JSON lines for one input. The real wrapper was not run end-to-end because the authoring sandbox refused the `HOME` override the fixture needs.

### D2 — Status-line wrapper leaks one temp file per refresh
- Location: `.moai/status_line.sh:23` (PATH tier), `:30` (absolute `/home/rico/.local/bin/moai`), `:35` (`$HOME/go/bin`), `:40` (`$HOME/.local/bin`); EXIT trap at `:8`; `mktemp` at `:7`; the file's own comment at `:20` states that `exec` replaces the shell. `statusLine.refreshInterval` is `10` at `.claude/settings.json:342`.
- Observed: `exec` replaces the shell, so `trap 'rm -f "$temp_file"' EXIT` never runs and the temp file stays.
- Reproduced by author: yes. The real `.moai/status_line.sh` run with a stub `moai` first on `PATH` and `TMPDIR` pointing at an empty scratch directory: 0 files before, 1 after one run (branch 1 only; branches 2-4 use the identical construct). Context, not attribution: `/tmp` holds about 2k `tmp.*` files that contain `"transcript_path"` (1824 at the authoring read, 2062 at the audit read), consistent with leaked status-line input and still growing.
- Related: the branch at `:29-31` hard-codes an author home path. A tracked file must not carry it (REQ-HOOKS-003); branches 3 and 4 already cover `$HOME`-relative installs.

### D3 — Navigator progress map shifts columns when an optional field is empty
- Location: `.claude/skills/moai-workflow-project/scripts/navigator-regen.sh:251` (`while IFS=$'\t' read -r id title status phase module sha ts`); rows are produced at `:180` and defaulted at `:178-179`. The `awk -F'\t'` consumers at `:212` and `:237` preserve empty fields.
- Derived by reading: tab is IFS whitespace, so consecutive tabs collapse. A SPEC without `phase` and/or `module` shifts later values left in `progress-map.md`; an id/title/status-only SPEC would show `(untracked)` in the phase column and empty provenance columns.
- Reproduced by author: mechanism only. In isolation, `read` on a row with an empty 4th field gave `phase=[some/module] module=[abc123] sha=[2026-10-18T00:00:00+00:00] ts=[]`, while `awk -F'\t'` on the same row gave `phase=[] module=[some/module] sha=[abc123] ts=[2026-10-18T00:00:00+00:00]`. The script itself was not run because it shells out to `git`.

### D4 — Sync-phase gate emits its Stop block decision inside `hookSpecificOutput`
- Location: `.claude/hooks/moai/sync-phase-quality-gate.sh:391-399` (blocking JSON at `:393-394`, advisory at `:396-397`). The script contradicts itself: the header (`:15`, `:35`) documents the top-level form `{"decision":"block", ...}`, while the comment at `:377-383` and `:387` asserts the nested form is "per the official Stop hook contract".
- Observed: blocking output is `{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":...},"systemMessage":...}`. The Codex review gate reportedly says installed Claude Code 2.1.302 accepts `decision`/`reason` at the top level only, so the block would not be enforced.
- Evidence found (none run against 2.1.302): (i) the public Claude Code hooks reference, "Stop decision control" (https://code.claude.com/docs/en/hooks, fetched 2026-10-18 through WebFetch; not pinned to a version), lists `decision` and `reason` as top-level Stop fields and `hookSpecificOutput.additionalContext` as the only nested Stop field; (ii) the Codex plugin's own Stop hook emits top-level `{decision:"block", reason}` (`stop-review-gate-hook.mjs:168-171`); (iii) the gate's own header at `:15` and `:35`; (iv) `.claude/rules/moai/core/hooks-system.md:103,388` are silent on the form. `claude --version` reports 2.1.302.
- Reproduced by author: no. Enforcement on 2.1.302 is measured by AC-HOOKS-008.

### D5 — Sync-phase gate skipped ruff because ruff is only in `.venv`
- Location: `.claude/hooks/moai/sync-phase-quality-gate.sh:228-241` (python branch), `run_step` at `:204-214`, log line at `:402`.
- Original behavior (backup `/home/rico/.claude/jobs/fadbe668/tmp/sync-phase-quality-gate.sh.bak`, a job-tmp file and the only copy): the python branch was `run_step ruff c1 ruff check .`. `run_step` records exit `0` with "skipped: ruff absent" when the tool is not on `PATH`, and the audit log records only `ruff=0`, so a skipped check is indistinguishable from a pass. In the authoring session `command -v ruff` exits 1 while `/home/rico/Desktop/Project/orbit-wizard-blue/.venv/bin/ruff` exists.
- Local patch (applied 2026-10-18 in the primary checkout, untracked): a `diff` of the backup against the current file differs only in lines 230-240; it prefers `$PROJECT_ROOT/.venv/bin/ruff` (or `.venv/Scripts/ruff.exe`) running `check src tests tools`, else falls back to `ruff check .` on `PATH`. The patch passes `src tests tools` unconditionally; a project missing one of them would get ruff error E902 (confirmed by the plan-audit), which the gate turns into a block (`:332-338`, blocking mode is the default). REQ-HOOKS-006 closes that.
- Reproduced by author: partial. The skip path is confirmed by reading. `.moai/logs/sync-quality-gate.log` is absent, so the recorded `ruff=0` was not observed. `.venv/bin/ruff check --no-cache src tests tools` was run by the author: `All checks passed!`. The full Stop-hook path has not been exercised.

## 2. Requirements (GEARS)

### REQ-HOOKS-001 — Stop-goal wrapper dispatches once, then exits 0
When a Stop event arrives for a session whose goal state file exists, the Stop-goal wrapper shall invoke `moai hook stop-goal` exactly once, using the first resolution tier that finds a binary, and then exit 0, preserving the wrapper's fail-open always-exit-0 contract (the evaluator's own exit status is not passed through); for a session with no armed goal it shall continue to exit 0 without invoking any `moai` binary.

### REQ-HOOKS-002 — Status-line wrapper cleans up its temp file
When the status-line wrapper resolves a `moai` binary in any resolution branch, it shall run that binary without replacing the wrapper shell, and shall exit with the binary's exit status so that its EXIT trap removes the temp input file.

### REQ-HOOKS-003 — Status-line wrapper carries no user-specific path
The tracked status-line wrapper shall contain no absolute path under a user home directory (`/home/<user>`, `/Users/<user>`, or `<drive>:\Users\<user>`) and shall resolve `moai` only through `PATH` and `$HOME`-relative locations.

### REQ-HOOKS-004 — Navigator parse preserves empty fields
When a SPEC's frontmatter omits an optional field (`phase` and/or `module`), the navigator regeneration script shall render every column of that SPEC's `progress-map.md` row from its own field, leaving empty fields empty and shifting no value into another column.

### REQ-HOOKS-005 — Sync-phase gate block is a top-level Stop decision
When the sync-phase quality gate runs in blocking mode and a structural check fails, the gate shall emit exactly one JSON object on stdout whose top-level keys are `decision` (value `"block"`), a non-empty `reason`, and `systemMessage`, with no `decision` key under `hookSpecificOutput`, and shall exit 0; in advisory mode or on pass it shall emit no `decision` key at any nesting level.

### REQ-HOOKS-006 — Sync-phase gate lints with the project's ruff, on existing directories only
While the detected project language is Python, the sync-phase quality gate shall run the project virtual environment's `ruff` (`$PROJECT_ROOT/.venv/bin/ruff` or `.venv/Scripts/ruff.exe`, whichever is executable) when one exists, else `ruff` from `PATH`, and shall pass `check` followed by only those of `src`, `tests`, `tools` that exist as directories under `$PROJECT_ROOT`, or `check .` when none of them exists.

### REQ-HOOKS-007 — Hardened files are tracked
The repository shall track exactly the four hardened files `.claude/hooks/moai/handle-stop-goal.sh`, `.claude/hooks/moai/sync-phase-quality-gate.sh`, `.claude/skills/moai-workflow-project/scripts/navigator-regen.sh`, and `.moai/status_line.sh` in git.

### REQ-HOOKS-008 — Scope preservation
The change shall not modify any tracked file other than the four files in REQ-HOOKS-007 (and this SPEC's own files), and shall not modify any other hook, the `moai` binary, or `AGENTS.md`.

## 3. Acceptance Criteria (inline, Tier S)

Conventions.
- `$REPO` is the checkout that contains the hardened files (the primary checkout until they are tracked). `$SCRATCH` is a new empty directory outside any git repository (for example `mktemp -d` under `/tmp`); run `export SCRATCH` so fixture child processes see it. `<base_sha>` is `git rev-parse HEAD` taken immediately before this SPEC's first run-phase edit and recorded in `progress.md` §E.2; the four tooling SPECs' run phases are executed one at a time, in the order HOOKS, ENV, GITOWN, REVGATE, so each name-only diff lists only this SPEC's files.
- Verification roles: the coordinator (orchestrator) runs every command in this section and records the verbatim output in `progress.md` §E.2; implementers only edit files and report. ACs marked **[coordinator-run]** call `git` (directly or through a script), run `moai`, or open a live Claude Code session; sub-agents run none of them.
- Gate commands are run as `env -u MOAI_SYNC_GATE_BLOCKING -u MOAI_AUTONOMY_TIER [VAR=value ...] CLAUDE_PROJECT_DIR=... bash <gate>`: the `-u` options come first, and any `VAR=value` assignment (for example `MOAI_SYNC_GATE_BLOCKING=0`) is written after them, otherwise the `-u` cancels it.
- Protected-file record (replaces the unverifiable `git diff` on untracked paths): at the first run edit the coordinator records in `progress.md` §E.2, in `sha256sum` format under `protected_sha256:`, the hashes of every `.claude/hooks/moai/*.sh` other than `handle-stop-goal.sh` and `sync-phase-quality-gate.sh`, and of the `moai` binary; at the end it writes those lines to `$SCRATCH/protected.sha256` and runs `sha256sum -c "$SCRATCH/protected.sha256"`.
- Scratch copy for `moai update`: `mkdir -p "$SCRATCH/updcopy" && tar -C "$REPO" --exclude=.git --exclude=.venv -cf - . | tar -C "$SCRATCH/updcopy" -xf -`, then `(cd "$SCRATCH/updcopy" && find . -type f | sort > "$SCRATCH/before.txt")`.

Fixture F1 (stub binaries; each stub appends its own path to `$SCRATCH/calls.log`, prints one JSON line, exits 7):
```
mkdir -p "$SCRATCH/bin" "$SCRATCH/tmp" "$SCRATCH/home/go/bin" "$SCRATCH/home/.local/bin" "$SCRATCH/proj/.moai/state/goal"
# for each of bin, home/go/bin, home/.local/bin create an executable file "moai" containing:
#   #!/bin/bash
#   cat >/dev/null
#   echo "$0" >> "$SCRATCH/calls.log"
#   echo '{"decision":"block"}'
#   exit 7
echo '{}' > "$SCRATCH/proj/.moai/state/goal/sess1.json"
```

### AC-HOOKS-001 — Stop-goal wrapper dispatches once and exits 0 (REQ-HOOKS-001) [coordinator-run]
- Given fixture F1 and `: > "$SCRATCH/calls.log"`
- When `printf '{"session_id":"sess1"}' | PATH="$SCRATCH/bin:/usr/bin:/bin" HOME="$SCRATCH/home" CLAUDE_PROJECT_DIR="$SCRATCH/proj" bash "$REPO/.claude/hooks/moai/handle-stop-goal.sh" > "$SCRATCH/out.txt"; echo "exit=$?"` is run
- Then it prints `exit=0`, `wc -l < "$SCRATCH/out.txt"` prints `1`, and `wc -l < "$SCRATCH/calls.log"` prints `1` (all three tiers resolvable; only the PATH tier ran)
- And with `PATH="/usr/bin:/bin"` instead, after `: > "$SCRATCH/calls.log"`, it prints `exit=0` and `calls.log` has exactly one line ending in `home/go/bin/moai`
- And with `PATH="/usr/bin:/bin"` and the `home/go/bin/moai` stub deleted, it prints `exit=0` and `calls.log` has exactly one line ending in `home/.local/bin/moai`
- And with `"session_id":"sess2"` (no goal state file) and the stubs restored, it prints `exit=0`, `out.txt` is empty, and `calls.log` stays empty
- And with all three stubs deleted it prints `exit=0` and `out.txt` is empty

### AC-HOOKS-002 — Status-line wrapper leaves no temp file and no home path (REQ-HOOKS-002, REQ-HOOKS-003) [coordinator-run]
- Given fixture F1 and an empty `$SCRATCH/tmp`
- When `grep -n -E '^[[:space:]]*exec[[:space:]]' "$REPO/.moai/status_line.sh"; echo "exit=$?"` is run
- Then it prints only `exit=1` (no executable `exec` line; the comment at `:20` does not match)
- And `grep -n -E '/(home|Users)/[^"/ ]+|[A-Za-z]:\\\\Users' "$REPO/.moai/status_line.sh"; echo "exit=$?"` prints only `exit=1`
- And `echo '{"x":1}' | PATH="$SCRATCH/bin:/usr/bin:/bin" HOME="$SCRATCH/home" TMPDIR="$SCRATCH/tmp" bash "$REPO/.moai/status_line.sh"; echo "exit=$?"` prints the stub's JSON line and `exit=7`, and `ls -A "$SCRATCH/tmp" | wc -l` prints `0`
- And the same run with `PATH="/usr/bin:/bin"` (stub only at `$HOME/go/bin`) prints `exit=7` with 0 files left, and with the `home/go/bin/moai` stub deleted (stub only at `$HOME/.local/bin`) prints `exit=7` with 0 files left

### AC-HOOKS-003 — Navigator preserves empty optional fields (REQ-HOOKS-004) [coordinator-run]
- Given `$SCRATCH/nav/.moai/specs/` containing three SPEC directories whose `spec.md` files carry only these frontmatter fields, each between `---` lines: `SPEC-NAVTEST-001` (`id`, `title: "No optional fields"`, `status: draft`), `SPEC-NAVTEST-002` (the same plus `phase: "v9.9.9 target"`), `SPEC-NAVTEST-003` (the same plus `phase: "v9.9.9 target"` and `module: "x/y"`)
- When `CLAUDE_PROJECT_DIR="$SCRATCH/nav" bash "$REPO/.claude/skills/moai-workflow-project/scripts/navigator-regen.sh"; echo "exit=$?"` is run
- Then it prints `exit=0`
- And in `$SCRATCH/nav/.moai/project/navigator/progress-map.md`, `grep -c -F -x '| SPEC-NAVTEST-001 | draft |  | (untracked) | (untracked) | draft |'` prints `1`, the same check for `'| SPEC-NAVTEST-002 | draft | v9.9.9 target | (untracked) | (untracked) | draft |'` prints `1`, and for `'| SPEC-NAVTEST-003 | draft | v9.9.9 target | (untracked) | (untracked) | draft |'` prints `1`
- And in `capability-map.md`, `grep -c -F -x '| SPEC-NAVTEST-001 | No optional fields | draft |  | (untracked) | (untracked) |'` prints `1` (regression guard: this table was already correct)

### AC-HOOKS-004 — Gate block is a top-level Stop decision (REQ-HOOKS-005) [coordinator-run]
- Given fixture F2: a scratch git repository `$SCRATCH/gate` (created by the coordinator) with `pyproject.toml`, `src/a.py`, an executable `.venv/bin/ruff` stub that writes its arguments to `$SCRATCH/ruff.argv` and exits 1, and a HEAD commit with subject `docs(SPEC-GATE-001): sync-phase fixture` that adds `src/a.py`
- When `cd "$SCRATCH/gate" && env -u MOAI_SYNC_GATE_BLOCKING -u MOAI_AUTONOMY_TIER CLAUDE_PROJECT_DIR="$SCRATCH/gate" bash "$REPO/.claude/hooks/moai/sync-phase-quality-gate.sh" > "$SCRATCH/gate.out"; echo "exit=$?"` is run
- Then it prints `exit=0` and `wc -l < "$SCRATCH/gate.out"` prints `1`
- And `python3 -c "import json; o=json.load(open('$SCRATCH/gate.out')); print(o.get('decision')=='block' and bool(o.get('reason')) and bool(o.get('systemMessage')) and 'decision' not in o.get('hookSpecificOutput', {}))"` prints `True`
- And `grep -n -F '"hookSpecificOutput":{"hookEventName":"Stop","decision"' "$REPO/.claude/hooks/moai/sync-phase-quality-gate.sh"; echo "exit=$?"` prints only `exit=1`
- And after `rm -f "$SCRATCH/gate/.moai/state/sync-quality-gate.last"`, the same command written as `env -u MOAI_SYNC_GATE_BLOCKING -u MOAI_AUTONOMY_TIER MOAI_SYNC_GATE_BLOCKING=0 CLAUDE_PROJECT_DIR="$SCRATCH/gate" bash "$REPO/.claude/hooks/moai/sync-phase-quality-gate.sh"` (assignment after the `-u` options) produces JSON with a `systemMessage` key and with no `decision` key at the top level or under `hookSpecificOutput`
- And after the same `rm`, with the stub changed to exit 0, `gate.out` is empty

### AC-HOOKS-005 — Gate runs the project ruff on existing directories (REQ-HOOKS-006) [coordinator-run]
- Given fixture F2 with the venv stub changed to exit 0, directories `src`, `tests`, `tools` all present, `: > "$SCRATCH/ruff.argv"`, and the sentinel `$SCRATCH/gate/.moai/state/sync-quality-gate.last` removed before each run
- When the AC-HOOKS-004 gate command is run with `PATH="/usr/bin:/bin"` (no `ruff` on PATH)
- Then `cat "$SCRATCH/ruff.argv"` prints `check src tests tools` and `gate.out` is empty
- And after deleting `$SCRATCH/gate/tools`, `cat "$SCRATCH/ruff.argv"` prints `check src tests`
- And after deleting `tests` and `src` as well, it prints `check .`
- And after deleting `$SCRATCH/gate/.venv` and putting a recording `ruff` stub first on `PATH`, with `src` and `tests` restored, `cat "$SCRATCH/ruff.argv"` prints `check src tests` (the `PATH` fallback uses the same directory selection)
- And with neither a venv ruff nor a `PATH` ruff, the gate prints `exit=0` and an empty `gate.out`

### AC-HOOKS-006 — Exactly the four hardened files are tracked and changed (REQ-HOOKS-007, REQ-HOOKS-008) [coordinator-run]
- Given the run-phase commit exists
- When `git ls-files --error-unmatch .claude/hooks/moai/handle-stop-goal.sh .claude/hooks/moai/sync-phase-quality-gate.sh .claude/skills/moai-workflow-project/scripts/navigator-regen.sh .moai/status_line.sh` is run
- Then it prints the four paths and exits 0
- And `git status --porcelain -- .claude/hooks/moai/handle-stop-goal.sh .claude/hooks/moai/sync-phase-quality-gate.sh .claude/skills/moai-workflow-project/scripts/navigator-regen.sh .moai/status_line.sh` prints nothing
- And `git diff --name-only <base_sha>..HEAD -- . ':(exclude).moai/specs'` prints exactly those four paths
- And `git diff --name-only <base_sha>..HEAD -- src tests tools packaging .github AGENTS.md` prints nothing
- And `sha256sum -c "$SCRATCH/protected.sha256"` reports `OK` for every recorded file (every other hook and the `moai` binary are unchanged)

### AC-HOOKS-007 — `moai update` treatment is measured (supports REQ-HOOKS-007) [coordinator-run]
- Given the scratch copy defined in Conventions (it contains the four hardened files), an empty `$SCRATCH/updhome`, and the output of `moai update --help` saved in `progress.md` §E.2
- When `cd "$SCRATCH/updcopy" && HOME="$SCRATCH/updhome" moai update --templates-only --no-hooks --yes` is run (always the real run in the scratch copy, `--templates-only` skips the binary update), followed by `cmp` of each of the four files against its `$REPO` version and `find . -type f | sort` diffed against `$SCRATCH/before.txt`, and `ls -R "$SCRATCH/updhome"`
- Then `progress.md` §E.2 holds the verbatim output, one line per file in the form `<path>: preserved` (cmp identical) or `<path>: overwritten-or-merged` (cmp differs, with the diff), the list of files the update created or changed, and the listing of any user-level state the command created under `$SCRATCH/updhome`
- If any file differs, the fix is not durable against `moai update`; this is reported as a Gap with the restoring step (reinstate the tracked version), and the finding is carried to the Kickoff decision.

### AC-HOOKS-008 — The installed Claude Code honors a top-level Stop block (REQ-HOOKS-005) [coordinator-run]
- Given a throwaway project at `$SCRATCH/probe` whose `.claude/settings.json` registers one Stop hook script that appends its stdin to `$SCRATCH/probe/stop.log` and prints `{"decision":"block","reason":"HOOKS001 probe"}` only on its first invocation
- When `cd "$SCRATCH/probe" && claude -p "reply with the word ok"` is run (Claude Code 2.1.302)
- Then `grep -c . "$SCRATCH/probe/stop.log"` prints `2` and the second logged payload contains `"stop_hook_active":true` (the block was honored and the turn continued)
- And, as an informational control, the same probe with the nested form `{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"HOOKS001 probe"}}` logs `1` invocation if the nested form is ignored
- If no live session can be run, this criterion is reported as a Gap, not a pass.

## 4. Exclusions

### Out of Scope — Application code
- No change under `src/`, `tests/`, `tools/`, `packaging/`, or `.github/`, and no change to `AGENTS.md`.

### Out of Scope — Other hooks and the moai binary
- No change to `handle-pre-tool.sh` (the reference pattern) or any other hook wrapper, and no change to the `moai` binary or its embedded templates.
- No change to hook registration in `.claude/settings.json` (owned by SPEC-ENV-001 where it concerns `env`).
- `navigator-audit.sh` uses the same tab-IFS `read` idiom (lines 522-526, 578-583) and is not changed here; no defect has been reported for it.

### Out of Scope — Environment, ownership, and review-gate issues
- The machine-specific `PATH` override is SPEC-ENV-001; the Git-ownership conflict is SPEC-GITOWN-001; the repeated Codex review-gate feedback is SPEC-REVGATE-001.

### Out of Scope — Cleanup and upstream reporting
- No deletion of the existing leaked temp files in `/tmp`.
- No edit of upstream issue #1827 and no upstream patch; reporting D4 and D5 upstream is a separate decision.
