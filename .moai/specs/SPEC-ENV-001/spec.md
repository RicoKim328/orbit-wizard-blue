---
id: SPEC-ENV-001
title: "Stop overriding PATH with a machine-specific list in shared Claude settings"
version: "0.3.0"
status: implemented
created: 2026-10-18
updated: 2026-10-18
author: Rico
priority: P2
phase: "v0.1.1 target"
module: ".claude/settings.json"
lifecycle: spec-anchored
tags: "settings, environment, path, venv, portability, claude-code, tooling"
tier: S
---

# SPEC-ENV-001: Stop overriding PATH with a machine-specific list in shared Claude settings

## HISTORY

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1.0 | 2026-10-18 | Rico | Initial draft (Tier S) |
| 0.2.0 | 2026-10-18 | Rico | Iteration 2 (plan-audit findings X-1..X-5, X-7..X-9, E-1..E-3): single tracking scope; PATH removal made conditional on `moai` resolving through the launching shell's PATH; hook-subprocess probe added; REQ-ENV-003 restated as a repository property; status-line path left to SPEC-HOOKS-001; always-real `moai update` measurement; coordinator-run marking |
| 0.3.0 | 2026-10-18 | Rico | Iteration 3 (re-audit E2-1..E2-5, C-1..C-3): AC-ENV-002 expects at least one `command -v moai` per wrapper; `$LAUNCH_PATH` is user-supplied and the probes run under an explicit `env PATH=` so replace-versus-merge is decidable; hook-probe fixture creates its directory; sha256 record replaces `git diff` on `.claude/hooks`; contiguous `base_sha`; defined scratch copy |

## 1. Context

The shared Claude Code settings file sets a literal `PATH` for every subprocess Claude Code starts. The Codex review gate reported this as a defect, as relayed by the coordinator; it is also listed in upstream issue https://github.com/modu-ai/moai-adk/issues/1827 (open, opened 2026-10-17, read through a WebFetch summary). Resolution direction (user decision): project-local hardening, tracked in git, in parallel with the upstream tracker. All line numbers were read on 2026-10-18 from `/home/rico/Desktop/Project/orbit-wizard-blue/.claude/settings.json` (untracked in the primary checkout, absent from this worktree).

### E1 — The `env` block replaces PATH with the author's Linux paths
- Location: `.claude/settings.json:349-356`, exactly:
  ```
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
    "ENABLE_TOOL_SEARCH": "1",
    "MOAI_CONFIG_SOURCE": "sections",
    "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1",
    "CLAUDE_CODE_NO_FLICKER": "1",
    "PATH": "/home/rico/.local/bin:/home/rico/go/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin"
  },
  ```
  The `PATH` value is on line 355. It is the only `/home/...` path in the file (a scan of the settings file, the hook wrappers, and the two scripts found the others only at `.moai/status_line.sh:29-30`).
- Observed in this authoring session: a Bash-tool `printenv PATH` returned exactly those eight entries, in that order, and `printenv MOAI_CONFIG_SOURCE` returned `sections`, so the `env` block is applied to tool subprocesses. `command -v ruff` exited 1 although `/home/rico/Desktop/Project/orbit-wizard-blue/.venv/bin/ruff` exists, and `VIRTUAL_ENV` was unset. The plan-audit session reproduced the same observation.
- A second observed consequence: `command -v node` resolves to `/usr/bin/node` (v12.22.9), and running the installed Codex plugin script (`/home/rico/.claude/plugins/cache/openai-codex/codex/1.0.6/scripts/codex-companion.mjs setup --json`) with it fails with `SyntaxError: Unexpected token '?'`. The author's Node v24.19.0 at `/home/rico/.nvm/versions/node/v24.19.0/bin/node` is not on the overridden PATH; the same script succeeds with that binary. Whether hook processes see the same PATH was not observed; AC-ENV-005 measures it.
- Not directly proven: that Claude Code replaces rather than merges the inherited PATH. The inherited value before the override was not captured; AC-ENV-004 records it. The observation is consistent with replacement but does not prove it.
- Consequences reported by the Codex gate as relayed by the coordinator, consistent with the observation: an activated project venv loses its executables; developers whose tools live in their own user dirs, Homebrew, or Windows locations lose them; hooks that resolve tools by name may fail or silently skip checks.
- Reproduced by author: partial (effective PATH observed; replace-versus-merge semantics and other developers' consequences are reported, not reproduced).

### E2 — Redundancy for the author's own tools
- `/home/rico/.bashrc:118,121` and `/home/rico/.profile:25-31,37` already prepend `$HOME/.local/bin` and `$HOME/go/bin` to PATH, so for a session launched from this author's bash the override adds entries the inherited PATH would normally already carry. Per the plan-audit, `~/.bashrc` also sources nvm after those exports, so removing the override changes `node` from v12.22.9 to v24.19.0 for such sessions, and the Codex plugin's `node` hooks would start running for real. Sessions launched without those startup files (for example from a desktop launcher) were not checked.

### E3 — `settings.local.json` is "not shared" only on this machine
- `.claude/settings.local.json` exists in the primary checkout (68 bytes, mode 0600; keys `enabledMcpjsonServers` and `teammateMode`).
- The repository `.gitignore` (both the primary checkout and this worktree) has no entry for it. It is excluded here only by the author's global ignore file, `/home/rico/.config/git/ignore:1` (`**/.claude/settings.local.json`). Other clones are not protected by that rule.

### E4 — `moai` resolution in the wrappers once PATH is inherited
- Three wrappers resolve `moai` without a `$HOME/.local/bin` tier: `handle-codex-review-gate.sh:62-74` (`$CLAUDE_PROJECT_DIR/../../moai`, `PATH`, `$HOME/go/bin/moai`), `handle-multi-review-gate.sh:66-79` (the same three), and `chain-event.sh:14-23` (`$CLAUDE_PROJECT_DIR/.moai/bin/moai`, `$HOME/go/bin/moai`, `command -v moai`). `moai` is installed at `/home/rico/.local/bin/moai` (the only copy found). Once the override is gone these wrappers find `moai` only if the launching shell's PATH carries it; otherwise they fail open silently. Wrappers that do have `$HOME` tiers: `handle-pre-tool.sh:71-81`, `handle-stop-goal.sh:69-76`. REQ-ENV-001 therefore applies only where `moai` resolves through the launching shell's PATH (AC-ENV-002), instead of editing the three wrappers.
- The hard-coded `/home/rico/.local/bin/moai` branch in `.moai/status_line.sh:29-31` is owned by SPEC-HOOKS-001 (REQ-HOOKS-003); this SPEC only references it.

### E5 — Interaction with the other tooling SPECs
- SPEC-HOOKS-001 (D5): the sync-phase gate prefers `$PROJECT_ROOT/.venv/bin/ruff`, so the gate no longer depends on this SPEC.
- SPEC-REVGATE-001 depends on this SPEC: with the override gone the MoAI Codex gate wrapper finds `moai` through the launching shell's PATH.

## 2. Requirements (GEARS)

### REQ-ENV-001 — No PATH in shared settings
Where `moai` resolves on the PATH of the shell that launches Claude Code, the shared `.claude/settings.json` `env` block shall not define `PATH`, and shall keep its other five entries (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, `ENABLE_TOOL_SEARCH`, `MOAI_CONFIG_SOURCE`, `CLAUDE_CODE_ENABLE_TODO_TOOLS`, `CLAUDE_CODE_NO_FLICKER`) with their values unchanged.

### REQ-ENV-002 — Inherited PATH reaches the session's subprocesses
When Claude Code is started from a shell whose PATH starts with an activated project virtual environment's `bin` directory, the session's Bash tool and a hook process shall each see that directory as the first PATH entry, so `ruff` resolves to the virtual environment's copy.

### REQ-ENV-003 — Local overrides are ignored by the repository itself
The repository's own `.gitignore` shall exclude `.claude/settings.local.json` from version control without relying on any global ignore file.

### REQ-ENV-004 — No home-directory paths in shared settings
The shared `.claude/settings.json` shall contain no absolute path under a user home directory (`/home/<user>`, `/Users/<user>`, or `<drive>:\Users\<user>`).

### REQ-ENV-005 — Exactly the changed files are tracked
The repository shall track exactly `.claude/settings.json` and `.gitignore` for this change, with `.claude/settings.json` carrying the content that satisfies REQ-ENV-001 and REQ-ENV-004.

### REQ-ENV-006 — Scope preservation
The change shall not modify any tracked file other than `.claude/settings.json` and `.gitignore` (and this SPEC's own files), any hook script, or the `moai` binary.

## 3. Acceptance Criteria (inline, Tier S)

Conventions.
- `$REPO` is the checkout that holds `.claude/settings.json`. `$SCRATCH` is a new empty directory outside any git repository (`export SCRATCH`). `<base_sha>` is `git rev-parse HEAD` taken immediately before this SPEC's first run-phase edit and recorded in `progress.md` §E.2; the four tooling SPECs' run phases are executed one at a time, in the order HOOKS, ENV, GITOWN, REVGATE, so each name-only diff lists only this SPEC's files. A pre-change copy of the file is saved in `progress.md` §E.2 as `$SCRATCH/settings.before.json`.
- `$LAUNCH_PATH` is supplied by the user, not observed: the coordinator session is daemon-spawned and cannot see the PATH of the shell the user launches Claude from (its own `printenv PATH` and its `/proc` environment both show the override literal). The coordinator asks the user to run `printenv PATH` in a normal interactive terminal and paste the result; it is recorded verbatim in `progress.md` §E.2 with the provenance `user-supplied`. If it was not supplied, AC-ENV-002, AC-ENV-004, and AC-ENV-005 are Gaps, not passes.
- Protected-file record (replaces `git diff` on untracked paths, which cannot fail): at the first run edit the coordinator records in `progress.md` §E.2, in `sha256sum` format under `protected_sha256:`, the hashes of every `.claude/hooks/moai/*.sh` and of `.claude/settings.local.json`; at the end it writes those lines to `$SCRATCH/protected.sha256` and runs `sha256sum -c "$SCRATCH/protected.sha256"`.
- Scratch copy for `moai update`: `mkdir -p "$SCRATCH/updcopy" && tar -C "$REPO" --exclude=.git --exclude=.venv -cf - . | tar -C "$SCRATCH/updcopy" -xf -`, then `(cd "$SCRATCH/updcopy" && find . -type f | sort > "$SCRATCH/before.txt")`.
- Verification roles: the coordinator (orchestrator) runs every command in this section and records the verbatim output in `progress.md` §E.2; implementers only edit files and report. ACs marked **[coordinator-run]** call `git`, run `moai`, or open a live Claude Code session; sub-agents run none of them.

### AC-ENV-001 — `env` no longer defines PATH (REQ-ENV-001)
- Given the change is applied to `.claude/settings.json`
- When `python3 -c "import json; e=json.load(open('.claude/settings.json'))['env']; print('PATH' in e); print(e == {'CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS':'1','ENABLE_TOOL_SEARCH':'1','MOAI_CONFIG_SOURCE':'sections','CLAUDE_CODE_ENABLE_TODO_TOOLS':'1','CLAUDE_CODE_NO_FLICKER':'1'})"` is run from `$REPO`
- Then it prints `False` then `True`
- And `diff "$SCRATCH/settings.before.json" .claude/settings.json | grep -c '^[<>]'` prints `3` (the `NO_FLICKER` line loses its trailing comma, the `PATH` line is deleted, nothing else changes)

### AC-ENV-002 — `moai` resolves through the launching shell's PATH (precondition of REQ-ENV-001) [coordinator-run]
- Given `$LAUNCH_PATH` supplied by the user and recorded in `progress.md` §E.2 (see Conventions)
- When `PATH="$LAUNCH_PATH" command -v moai` is run, and `grep -c -F 'command -v moai' "$REPO/.claude/hooks/moai/handle-codex-review-gate.sh" "$REPO/.claude/hooks/moai/handle-multi-review-gate.sh" "$REPO/.claude/hooks/moai/chain-event.sh"` is run
- Then the first prints a path, and the second prints `<path>:N` with `N` at least `1` for each of the three files (each resolves `moai` through `PATH`; the counts read on 2026-10-18 are 2, 2, and 1)
- If the first command prints nothing, or `$LAUNCH_PATH` was not supplied, the `PATH` entry is not removed and the finding goes to the orchestrator as a blocker report or a Gap.

### AC-ENV-003 — No home-directory path remains (REQ-ENV-004)
- Given the change is applied
- When `grep -n -E '/(home|Users)/[^"/ ]+|[A-Za-z]:\\\\Users' .claude/settings.json; echo "exit=$?"` is run from `$REPO`
- Then it prints only `exit=1`

### AC-ENV-004 — Inherited PATH and venv reach the Bash tool (REQ-ENV-002) [coordinator-run]
- Given `$LAUNCH_PATH` supplied by the user (a Gap if absent), and an explicit launch environment that simulates an activated venv: `env PATH="$REPO/.venv/bin:$LAUNCH_PATH"`
- And the baseline recorded before the change, with the original `settings.json` (override present): `cd "$REPO" && env PATH="$REPO/.venv/bin:$LAUNCH_PATH" claude -p "Use the Bash tool to run: printenv PATH | cut -d: -f1; command -v ruff; command -v node. Print only the output."`; a first line `/home/rico/.local/bin` means the override replaces the inherited PATH, a first line `$REPO/.venv/bin` means it merges
- When the same command is run after the change
- Then the first line equals `$REPO/.venv/bin`, the second line equals `$REPO/.venv/bin/ruff`, and the third line equals the `command -v node` that `PATH="$REPO/.venv/bin:$LAUNCH_PATH" command -v node` prints (baseline under the override: `/usr/bin/node`)
- If no session can be started for the probe, the criterion is reported as a Gap, not a pass. This probe relies on the model reproducing tool output; the deterministic evidence is AC-ENV-005.

### AC-ENV-005 — Inherited PATH reaches a hook process (REQ-ENV-002) [coordinator-run]
- Given `$LAUNCH_PATH` supplied by the user (a Gap if absent), `export REPO`, `mkdir -p "$SCRATCH/hookprobe/.claude"`, and a throwaway project at `$SCRATCH/hookprobe` whose `.claude/settings.json` is built from the changed file's `env` block plus one SessionStart hook: `python3 -c "import json,os; e=json.load(open(os.environ['REPO']+'/.claude/settings.json'))['env']; s=os.environ['SCRATCH']; json.dump({'env':e,'hooks':{'SessionStart':[{'hooks':[{'type':'command','command':'printenv PATH > '+s+'/hook.path'}]}]}}, open(s+'/hookprobe/.claude/settings.json','w'))"`
- When `cd "$SCRATCH/hookprobe" && env PATH="$REPO/.venv/bin:$LAUNCH_PATH" claude -p "reply with the word ok"` is run
- Then `cut -d: -f1 "$SCRATCH/hook.path"` prints `$REPO/.venv/bin`
- If no session can be started, the criterion is reported as a Gap, not a pass; the Bash-tool result alone does not establish the hook-subprocess half of REQ-ENV-002.

### AC-ENV-006 — The repository ignores local overrides (REQ-ENV-003) [coordinator-run]
- Given the change is applied to `.gitignore`
- When `git -c core.excludesFile=/dev/null check-ignore -q .claude/settings.local.json; echo "exit=$?"` is run from `$REPO`
- Then it prints `exit=0` (the repository's own rules ignore the file even with the global ignore file disabled)
- And `git diff <base_sha>..HEAD -- .gitignore | grep -E '^\+[^+]'` prints only lines that add ignore entries, and `git diff <base_sha>..HEAD -- .gitignore | grep -E '^-[^-]'; echo "exit=$?"` prints only `exit=1` (no removed or reordered line)

### AC-ENV-007 — Exactly two files are tracked and changed (REQ-ENV-005, REQ-ENV-006) [coordinator-run]
- Given the run-phase commit exists
- When `git ls-files --error-unmatch .claude/settings.json .gitignore; git status --porcelain -- .claude/settings.json .gitignore` is run
- Then both paths are printed and the status output is empty
- And `git show HEAD:.claude/settings.json > "$SCRATCH/tracked.json"` followed by AC-ENV-001 and AC-ENV-003 on that copy passes
- And `git diff --name-only <base_sha>..HEAD -- . ':(exclude).moai/specs'` prints exactly `.claude/settings.json` and `.gitignore`
- And `sha256sum -c "$SCRATCH/protected.sha256"` reports `OK` for every recorded file (the hook scripts and `.claude/settings.local.json` are unchanged; a `git diff` on these untracked paths could not fail)

### AC-ENV-008 — `moai update` treatment is measured (supports REQ-ENV-005) [coordinator-run]
- Given the scratch copy defined in Conventions (it contains the changed `.claude/settings.json`), an empty `$SCRATCH/updhome`, and `moai update --help` output saved in `progress.md` §E.2
- When `cd "$SCRATCH/updcopy" && HOME="$SCRATCH/updhome" moai update --templates-only --no-hooks --yes` is run (always the real run in the scratch copy), followed by `cmp .claude/settings.json "$REPO/.claude/settings.json"`, `python3 -c "import json; print('PATH' in json.load(open('.claude/settings.json'))['env'])"`, and `ls -R "$SCRATCH/updhome"`
- Then `progress.md` §E.2 holds the verbatim output, `.claude/settings.json: preserved` (cmp identical) or `.claude/settings.json: overwritten-or-merged` (with the diff), the printed `True`/`False` for `PATH`, and the listing of any user-level state created under `$SCRATCH/updhome`
- If `PATH` reappears or the file differs, the fix is not durable against `moai update`; this is reported as a Gap with the restoring step and carried to the Kickoff decision. The same scratch run on the original (pre-change) file records whether `moai update` writes the `PATH` entry, which answers where the entry came from.

## 4. Exclusions

### Out of Scope — Other settings content
- No change to hook registrations, permissions, `statusLine`, model, or output style in `.claude/settings.json`.
- No change to the five remaining `env` entries.

### Out of Scope — Other files and the status-line path
- `.moai/status_line.sh:29-31` (`/home/rico/.local/bin/moai`) is owned by SPEC-HOOKS-001 (REQ-HOOKS-003); it is not edited here.
- No change to the hook wrappers (including the three that lack a `$HOME/.local/bin` tier), to `.claude/settings.local.json` content on any machine, or to shell startup files.

### Out of Scope — Tooling internals
- No change to the `moai` binary or the `moai update` template set.

### Out of Scope — Upstream
- No edit of upstream issue #1827 and no upstream patch.
