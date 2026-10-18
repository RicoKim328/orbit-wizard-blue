# SPEC-REVGATE-001 — Progress

## §E.1 Plan-phase Audit-Ready Signal

Plan-phase notes (authoring session 2026-10-18, iteration 1):
- The repetition itself was not observed by the author (relayed by the coordinator). Knobs listed in `spec.md` §1 G2 were verified by reading; the Go handler was not readable, only `strings` of the binary.
- Read-only runtime reads: MoAI gate toggle `True`, plugin gate `reviewGateEnabled=False` in two workspaces (Node v24.19.0).

Iteration 2 (2026-10-18), addressing `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18.md`:
- X-1..X-5, X-7..X-10 and R-1..R-10 addressed (markers removed; single tracking scope; coordinator-run marking; always-real `moai update` measurement; stub-only PATH dir for the codex-absent case; `fixed-in` never suppresses; MoAI-gate scoping; provenance reworded; `~/...` citations; hard `depends_on`).

Post-iteration-3 (2026-10-18), addressing `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18-iter3.md` (applied by the coordinator, not re-audited):
- R3-1 (major): fixed in AC-REVGATE-004. The date check no longer uses interval expressions, which this host's mawk does not support. Checked by hand on this host: a valid `2026-10-18` row prints nothing; a `26-10-18` row is reported.
- R3-2 (major): fixed in AC-REVGATE-003. Two cases added: an unparsed third bullet, and a block with no bullets; both require `cmp` to report identical. Not executed (the AC needs the run-phase wrapper).
- R3-3..R3-10 and the other SPECs' iteration-3 minors are recorded as known debt in `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18-iter3.md`.

Iteration 3 (2026-10-18), addressing `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18-iter2.md` and the coordinator-captured `observed-gate-output.md`:
- R2-1 (blocker): fixed. The register's match key now comes from the verbatim titles and paths in `observed-gate-output.md`; each entry's evidence field names the sample and item, and AC-REVGATE-004 verifies against that file, not against current source lines. The reviewer-cited source lines are snapshotted below at plan time.
- R2-2 (major): fixed. Handler-shape run-phase dependency deleted; Shapes T and N removed; REQ-REVGATE-003/004 and AC-REVGATE-003 are stated for the observed shape only, with identity = normalized title + path (line ranges ignored, said explicitly). The former capture task became a one-time re-confirmation (plan §C step 3 = AC-REVGATE-003 step 0) that fails the SPEC if the shape differs.
- R2-3 (major): fixed. AC-REVGATE-005 adds stub-handler cases for no output, a timeout-style exit status, and non-block output; REQ-REVGATE-005 narrowed to what the wrapper controls.
- R2-4: fixed (REQ-REVGATE-007 now says byte-identical, no informational text). R2-5: fixed (six fields, no header or comment lines; the AC awk rejects them). R2-6: fixed (AC-REVGATE-001 runs per workspace root; host paths for `$NODE`/`$CODEX_COMPANION` moved to `progress.md` §E.2). R2-7: fixed (G4 states the active population is empty at seed time and what the register is for). R2-8 and C-1: fixed (sha256 record `protected_sha256:` replaces `git diff` on `.moai/config`, hooks, the plugin, and the binary). C-2: fixed (`base_sha` taken immediately before the first run edit; run phases one at a time, order HOOKS, ENV, GITOWN, REVGATE). C-3: fixed (scratch copy defined with `tar`, file list before/after).
- `plan_status` stays audit-ready: every blocker and major finding is fixed.

Plan-time source snapshot (verbatim lines the reviewer cited, primary checkout, 2026-10-18; supporting evidence only, the register keys on the observed finding text):
- `.claude/hooks/moai/handle-stop-goal.sh:64-66`: `if command -v moai &> /dev/null; then` / `    printf '%s' "$INPUT" | exec moai hook stop-goal 2>>"$MOAI_HOOK_STDERR_LOG"` / `fi`
- `.moai/status_line.sh:22-24`: `if command -v moai &> /dev/null; then` / `	exec moai statusline < "$temp_file"` / `fi`
- `.claude/skills/moai-workflow-project/scripts/navigator-regen.sh:251-252`: `        while IFS=$'\t' read -r id title status phase module sha ts; do` / `            fmilestone="$status"`
- `.claude/settings.json:355`: `    "PATH": "/home/rico/.local/bin:/home/rico/go/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin"`
- `.claude/hooks/moai/sync-phase-quality-gate.sh:381-384` (comment lines, the range the reviewer cited): `# hook contract (a bare top-level "decision" field is non-compliant for Stop).` / `# The hook still exits 0: per Claude Code hook semantics, stdout JSON is honored` / `# only on exit 0 (on exit 2 stdout is discarded and only stderr is surfaced).` / `#`; the emission is at `:393-394` (`printf '{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"%s"},...`)
- `.claude/hooks/moai/sync-phase-quality-gate.sh:228-230`: `    python)` / `        C1_LABEL="ruff"` / `        # Prefer the project virtual environment's ruff (AGENTS.md lint command);` (the original, unpatched branch was `run_step ruff c1 ruff check .`)
- `.claude/agents/moai/manager-git.md:4-5`: `  Git workflow specialist. Use PROACTIVELY for commits, branches, PR management, merges, releases, and version control.` / `  Invocation gate: invoked for PR creation across ALL tiers (S/M/L) per the PR-mandatory policy (enforce_admins: true). ...`

plan_status: audit-ready
plan_complete_at: 2026-10-18

## §E.2 Run-phase Evidence

_<pending run-phase>_

## §E.3 Run-phase Audit-Ready Signal

_<pending run-phase>_

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase>_
