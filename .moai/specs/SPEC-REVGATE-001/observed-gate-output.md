# Observed review-gate output (verbatim, coordinator-captured)

Source: two consecutive Stop-hook feedback messages received by the coordinator session on 2026-10-18 (hook: `handle-codex-review-gate.sh`, text prefix `codex review gate:`). Captured by the coordinator from the live session; nothing below was written by a SPEC author. Only the findings text is reproduced; the surrounding hook wrapper line (`Stop hook blocking error from command: "bash -c [ -f "$0" ] && exec bash "$0"; ... handle-codex-review-gate.sh": ...`) repeats the same summary + findings verbatim after the prefix.

## Shape observed

```
Stop hook feedback:
codex review gate: <one-paragraph summary>

Full review comments:

- [P2] <title> — <absolute path>:<line or line-range>
  <body paragraph(s), indented two spaces>

- [P2] ...
```

Observed facts: findings are a bullet list; severity tag `[P2]` on every item seen; title and `path:lines` are separated by ` — ` (em dash); body is indented two spaces; the summary line mentions test/Ruff results and "live ... integration was not tested". Finding SETS differ between runs (see sample A vs B: sample B adds two findings and drops two).

## Sample A (first message)

```
codex review gate: The new tooling contains reproducible hook and navigator defects, a nonportable PATH override, and conflicting Git ownership instructions. Application verification passed with 169 tests and clean Ruff results; live Claude and GitHub Actions integration was not exercised.

Full review comments:

- [P2] Keep Git operations with Astra — /home/rico/Desktop/Project/orbit-wizard-blue/.claude/agents/moai/manager-git.md:4-5
  This agent explicitly delegates commits, pushes, and PR creation to sub-agents, contrary to the repository's [Astra-only Git rule](AGENTS.md#L13). Following the new workflow would bypass that ownership boundary. Adapt the agent and its routing instructions to return proposed repository actions to Astra rather than execute them.

- [P2] Exit after invoking the resolved goal-hook binary — /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-stop-goal.sh:64-66
  When a goal is armed and `~/.local/bin/moai` is also on PATH, the handler runs twice: `exec` replaces only the pipeline subprocess, so the parent continues into the fallback branches. An isolated reproduction emitted two JSON decisions for one hook event. This can repeat goal-state updates and produce an invalid combined response. Exit after the first invocation or resolve the binary once before invoking it.

- [P2] Remove the machine-specific shared PATH override — /home/rico/Desktop/Project/orbit-wizard-blue/.claude/settings.json:355-355
  This replaces every Claude subprocess's inherited PATH with Rico's Linux paths. An activated project virtual environment loses its executables, and other developers lose tools installed in their own user directories, Homebrew, or Windows locations. Hooks can consequently fail to resolve installed tools or silently skip checks. Preserve the inherited PATH and keep machine-specific overrides in local settings.

- [P2] Preserve empty columns when reading navigator rows — /home/rico/Desktop/Project/orbit-wizard-blue/.claude/skills/moai-workflow-project/scripts/navigator-regen.sh:251-251
  When a SPEC omits optional `phase` or `module` fields, Bash treats consecutive tab separators as whitespace and collapses them. The remaining values shift into earlier variables, corrupting the progress map's phase and commit provenance. A SPEC containing only id, title, and status reproduced `(untracked)` as its phase with empty commit columns. Parse the rows with a method that preserves empty TSV fields.

- [P2] Allow the status-line temporary-file cleanup to run — /home/rico/Desktop/Project/orbit-wizard-blue/.moai/status_line.sh:22-24
  Whenever `moai` resolves successfully, `exec` replaces the shell without running its EXIT trap, leaving the temporary input file behind. An isolated invocation confirmed the file remained after completion. Because this script runs repeatedly for status updates, temporary files accumulate throughout normal sessions. Invoke the binary without replacing the shell, then propagate its exit status after cleanup.
```

## Sample B (a later message, different set)

```
codex review gate: All 169 application tests and Ruff passed, but the new tooling contains reproducible hook, validation, reporting, and cleanup defects. Live GitHub workflows and a full Claude session were not tested.

Full review comments:

- [P2] Exit after dispatching the goal hook — /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-stop-goal.sh:64-66
  With an armed goal and MoAI installed in `~/.local/bin` on PATH, this executes the evaluator twice. ... Exit after the first dispatch, as `handle-pre-tool.sh` does.

- [P2] Emit the Stop decision at the top level — /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/sync-phase-quality-gate.sh:381-384
  When a structural check fails, the blocking decision is placed inside `hookSpecificOutput`. The installed Claude Code 2.1.302 schema accepts Stop `decision` and `reason` at the top level; its Stop-specific object only accepts `additionalContext`. ... Move `decision` and `reason` to the top-level response.

- [P2] Run Ruff from the project virtual environment — /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/sync-phase-quality-gate.sh:228-230
  For the documented development setup, Ruff is installed in `.venv`, but this checks only the global PATH ... the gate therefore records `ruff=0` and allows completion without running any check ... Resolve the project interpreter and use the lint command specified in AGENTS.md:23.

- [P2] Preserve empty fields when reading navigator rows — /home/rico/Desktop/Project/orbit-wizard-blue/.claude/skills/moai-workflow-project/scripts/navigator-regen.sh:251-252
  (same defect as sample A, new line range 251-252)

- [P2] Allow status-line cleanup to run after MoAI exits — /home/rico/Desktop/Project/orbit-wizard-blue/.moai/status_line.sh:22-24
  (same defect as sample A, reworded title)
```

(Bodies in sample B are abridged with `...` by the coordinator for this file; sample A is complete. The coordinator observed 5 such messages in total on 2026-10-18, each with a different finding set and wording; the same defects recur under different titles and slightly shifted line ranges.)
