# Plan-phase re-audit (iteration 2/3): SPEC-HOOKS-001, SPEC-ENV-001, SPEC-GITOWN-001, SPEC-REVGATE-001

Date: 2026-10-18. Auditor: plan-auditor (read-only; no git/gh run, no SPEC or tooling file edited, no agent spawned).
Reasoning context ignored per M1 Context Isolation; the four user decisions passed in the prompt were treated as fixed inputs and only checked for consistent implementation. `progress.md` dispositions were not trusted; every fix below was re-read in the text.
Cross-model audit (codex/glm/audit_multi): not invoked (no `audit_model` configured; the codex reviewer would re-run the gate under study).
Scope of re-audit: the iteration-1 delta (X-1..X-10, H-*, E-*, G-*, R-*), re-verification of new factual claims against the real files, and new defects introduced by the revision.

## 1. Verdicts

| SPEC | Tier / threshold | Score | Verdict | Ready for Kickoff Approval |
|---|---|---|---|---|
| SPEC-HOOKS-001 | S / 0.75 | 0.90 | PASS-WITH-FIXES (minor only) | yes |
| SPEC-ENV-001 | S / 0.75 | 0.84 | PASS-WITH-FIXES (2 major, one-line fixes) | no |
| SPEC-GITOWN-001 | M / 0.80 | 0.83 | PASS-WITH-FIXES (1 major) | no |
| SPEC-REVGATE-001 | S / 0.75 | 0.69 | FAIL (1 blocker, 2 major; below threshold) | no |

Ready for Kickoff Approval: HOOKS yes; ENV no; GITOWN no; REVGATE no.

Category scores (rubric bands): HOOKS Clarity 0.90 / Completeness 1.00 / Testability 0.85 / Traceability 1.00. ENV 0.85 / 1.00 / 0.65 / 1.00. GITOWN 0.85 / 0.95 / 0.70 / 1.00. REVGATE 0.65 / 0.90 / 0.50 / 0.75.

## 2. Must-pass results (all four unless noted)

- MP-1 REQ numbering: PASS. HOOKS REQ-001..008 (spec.md:62-84), ENV 001..006 (:66-82), GITOWN 001..007 (:89-108), REVGATE 001..008 (:57-79). No gaps or duplicates. REQ/AC counts vs ceilings (spec-workflow.md:146-150): HOOKS 8/8 (S<=8, at ceiling), ENV 6/8, GITOWN 7/13 (M<=16), REVGATE 8/8 (at ceiling). No ceiling exceeded; HOOKS and REVGATE have no headroom for a new REQ or AC.
- MP-2 GEARS: PASS, judged on the REQ layer in spec.md (ACs are Given-When-Then, correct for the verification layer; acceptance.md for GITOWN). All REQs are event-driven, state-driven, Where, ubiquitous or negative. Weak spot: REQ-REVGATE-003 ends with a second sentence ("Findings are delimited ... as recorded for the handler's output shape", spec.md:64) with no `shall` (see R2-5).
- MP-3 frontmatter: PASS. All 12 canonical fields plus `tier` present and correctly typed in all four (spec.md:1-15/16). `phase: "v0.1.1 target"` is a release label (not a prohibited stage name). `related_specs` is gone (grep: no hit). REVGATE `depends_on: [SPEC-HOOKS-001, SPEC-ENV-001, SPEC-GITOWN-001]` (:15) is a documented optional key.
- MP-4 language neutrality: N/A (project-local Python repo).
- MP-5 D7: PASS. Referenced IDs: HOOKS/ENV/GITOWN/REVGATE (all `status: draft`, verified by `grep '^status:'`). `SPEC-GATE-001` (HOOKS spec.md:130) and `SPEC-NAVTEST-001/2/3` (HOOKS :123) are fixture literals, so the D7-5 "not found" SHOULD is a false positive. No retired/superseded/archived reference.
- MP-6 D8: PASS (auto). `syscall` count is 0 in every artifact of all four SPECs.
- MP-7 clarification gate: PASS. `grep '\[NEEDS CLARIFICATION'` in all plan.md, spec.md, acceptance.md, spec-compact.md: zero hits. The only hits are descriptive prose in each `progress.md` iteration-2 entry (HOOKS progress.md:10, ENV :10, GITOWN :10, REVGATE :11: "all `[NEEDS CLARIFICATION]` markers removed"), which have no `: topic` and are outside the plan.md/research.md scope of MP-7. Optional: reword them so a recursive grep stays clean.

## 3. Verification of every iteration-1 claim (re-read in the text)

Cross-cutting
- X-1 clarification gate: RESOLVED. No markers in any plan.md; all four plans end with "Open decisions for Kickoff Approval: None" (HOOKS plan.md:94-96, ENV :86-88, REVGATE :100-102) or "Decisions recorded" (GITOWN plan.md:105-107). Measurements moved to plan §C. Residual: GITOWN progress.md:10 still says "One item under 'Open decisions for Kickoff Approval'" while plan.md:105-107 says it is decided (G2-4).
- X-2 single tracking scope: RESOLVED. REQ-HOOKS-007 (:81), REQ-ENV-005 (:78), REQ-GITOWN-007 (:107), REQ-REVGATE-006 (:72) name exact files; no "plus any file added" text remains (grep: none).
- X-3 status-line path ownership: RESOLVED. HOOKS REQ-HOOKS-003 (:68) + plan task 5 (plan.md:46) delete `status_line.sh:29-31`; ENV excludes it (spec.md:58, :147).
- X-4 `moai update` ACs: RESOLVED in logic. Always-real scratch run with isolated `HOME`, decided from `cmp` (AC-HOOKS-007, AC-ENV-008, AC-GITOWN-013, AC-REVGATE-008). Flags verified with `moai update --help`: `--templates-only`, `--no-hooks`, `--yes` all exist. Residual: C-3.
- X-5 coordinator-run marking: RESOLVED. HOOKS spec.md:90, ENV :88, GITOWN acceptance.md:8, REVGATE spec.md:85.
- X-7 `related_specs`: RESOLVED. X-8 process REQs: RESOLVED (now measurement ACs). X-9 provenance: RESOLVED ("as relayed by the coordinator" at HOOKS :28, ENV :28/:46, GITOWN :30, REVGATE :29). X-10 sequencing noise: RESOLVED (HOOKS plan.md:23 and R5, ENV plan.md:22, GITOWN plan.md:26, REVGATE plan.md:27).

HOOKS: H-1 RESOLVED (REQ-HOOKS-005 pinned top-level, :74-75; AC-HOOKS-004 asserts it; AC-HOOKS-008 is the live check). H-2 RESOLVED (REQ-HOOKS-001 states exit 0, evaluator status not passed through, :63; matches today's behavior, `handle-stop-goal.sh:79`). H-3 RESOLVED (REQ-HOOKS-006 and AC-HOOKS-005 select existing directories; application-lint bullet removed). H-4 RESOLVED (`export SCRATCH`, :89). H-5 RESOLVED (plan.md:42 edits only 377-383 and 387; D4 cites :15 and :35). H-6 RESOLVED (clause dropped). H-7 RESOLVED (RED baseline, plan.md:19). H-8 RESOLVED (:176). H-9 RESOLVED (plan.md R2). H-10 RESOLVED (:91). H-11 RESOLVED (spec-compact.md:7 heading now neutral).
ENV: E-1 RESOLVED in text (REQ-ENV-002 keeps the hook half, AC-ENV-005 probes a hook process; but see E2-2, E2-3). E-2 PARTIAL (REQ-ENV-001 is conditional, E4 and R1 cover all three wrappers, R2 notes node; the precondition itself is flawed, E2-1/E2-2). E-3 RESOLVED (REQ-ENV-003 restated, :72-73).
GITOWN: G-1 RESOLVED (`tier: M` at :14, acceptance.md present, 7 REQ / 13 AC, 14 files within 5-15). G-2 RESOLVED (spec-workflow.md not edited; override rule REQ-GITOWN-003; but its check is vacuous, G2-1). G-3 RESOLVED with minor inventory gaps (G2-2). G-4 RESOLVED (AC-GITOWN-010 carve-out grep, AC-GITOWN-011 includes "run git status"). G-5 RESOLVED (sentence uses "orchestrator (Astra)"). G-6 RESOLVED (3 trials, no remote, no gh auth). G-7 RESOLVED (wording removed).
REVGATE: R-1 RESOLVED (AC-REVGATE-005 uses `$SCRATCH/onlymoai` and proves codex excluded; I confirmed `PATH=/usr/bin:/bin command -v codex` exits 1 and the `VAR=... command -v` idiom honors the temporary PATH). R-2 PARTIAL (shape-conditional, R2-2). R-3 NOT RESOLVED (R2-1). R-4 RESOLVED (`fixed-in` never suppresses: REQ-REVGATE-004/-007, plan §D). R-5 RESOLVED (:29). R-6 RESOLVED (REQ-003/-005/-007 say "Where the MoAI gate is enabled"; REQ-001 keeps the plugin gate off). R-7 RESOLVED (plan.md:43 non-gating). R-8 RESOLVED (workflow.yaml not tracked). R-9 RESOLVED (`~/...`, AC-REVGATE-002). R-10 RESOLVED (hard dependency, plan §C1).

## 4. Re-verification of new factual claims against the real files

Confirmed exact:
- `sync-phase-quality-gate.sh`: nested-form assertions at `:377-383` and `:387` (line 381 "a bare top-level \"decision\" field is non-compliant"; 387 "nested \"decision\":\"block\" stdout field"); header documents the top-level form at `:15` and `:35`; python branch `:228-241`; block/advisory printf `:393-394`/`:396-397`; decision logic `:332-338`; subject trigger `*"docs("*"): sync-phase"*` accepts the fixture subject in AC-HOOKS-004.
- `.moai/status_line.sh`: mktemp `:7`, trap `:8`, comment `:20`, `exec` at `:23`, `:30`, `:35`, `:40`, absolute `/home/rico/.local/bin/moai` branch `:29-31`. `settings.json`: `refreshInterval: 10` at `:342`; `env` block `:349-356`; PATH at `:355`, the only `/home/` hit (grep). Stop registration of `handle-codex-review-gate.sh` at `:144-149` with `timeout: 900`.
- GITOWN added inventory lines, each read: `run.md:51` ("git operations (Phase 19)"), `:152` ("surfaced via git status"); `plan.md:97` ("gh issue create"); `sync.md:52` ("Phase 13 Git Operations"), `:126` (Phase 13 comment); `sync/delivery.md:46` ("git commit operations"), `:448` ("syncs based on git diff"); `manager-develop.md:234` ("isolated git worktree"). All accurate.
- All old strings used by AC-GITOWN-001/003 exist verbatim today (RED is real): manager-git description/`push + PR is always delegated to manager-git`, manager-develop `- Commit changes, update SPEC status` and `| Git operations | manager-git |`, manager-docs `verification before committing`, manager-lead `or handles Tier S/M push+PR directly`, task-decomposition `Agent: manager-git subagent`/`- Push the commit(s) to`/`no separate agent spawn for git operations`, spec-assembly and delivery `Agent: manager-git subagent`, delivery `manager-docs creates the single sync commit directly on`/`manager-git creates the same single sync commit`/`Verify commit with`, mode-orchestration `Phase 19: manager-git created commits`, run.md `surfaced via git status`, CLAUDE.md `3. PR creation (Tier L OR`. Caveat: `grep -c -F '- Git ...'` without `-e` is read as an option by ugrep; the ACs correctly use `-e`.
- `navigator-regen.sh`: progress-map row is `| id | status | phase | sha | ts | fmilestone |` (`:241-242,255-257`) with `(untracked)` sentinels (`:164-165`), so the expected rows in AC-HOOKS-003 are exact; the unfixed `read` (`:251`) turns row 001 into `| SPEC-NAVTEST-001 | draft | (untracked) |  |  | draft |`, so RED is real. capability-map uses `awk -F'\t'` (`:238`) so the regression-guard row is correct.
- AC-HOOKS-001..005 fixtures (traced against `handle-stop-goal.sh:44-79` and the gate): runnable by the coordinator as written; the unfixed wrapper prints 3 lines/3 calls (RED), the fixed one 1/1.

The GITOWN awk scan (Scan S), run against the real unchanged files:
- It FAILS while imperative text remains: it prints manager-git.md 31, 32, 40-42, 92, 96-99, 104-105, 110-114, 119-122, 125, 127, 137, 156, 160, 168-170; delivery.md 42, 46, 229-231, 241, 253, 262, 267, 272, 278, 289, 297-298, 303, 316-318, 328-330, 448; spec-assembly.md 274, 280, 281, 312, 314, 336; run.md 152, 165; plan.md 97; manager-develop.md 234. This covers every RED line the AC claims.
- It CAN pass afterward: a synthetic test (stdin, no file written) showed a labeled fenced block is skipped, an unlabeled block and a label separated by a blank line are flagged, and the prohibition sentence ("runs git or gh") is not flagged. Verb frequency across the 13 files shows no imperative verb outside the scan's list today.
- Limits: (a) it flags non-imperative prose (manager-docs.md:8 "NOT for: ... git branch management", run.md:165, manager-git.md:125 prohibition), so rewrites must also touch these; (b) three hits are not in the inventory or the plan file table: manager-docs.md:8, run.md:165, spec-assembly.md:336 (G2-2); (c) the verb list omits `git -C|config|show|ls-files|clone|init|restore|cherry-pick|remote` and `gh api|run|release|repo|auth`, harmless today but a rewrite could add them unflagged (G2-3); (d) `run.md:51`, `sync.md:52,126`, `mode-orchestration.md:78` and `task-decomposition.md` contain no `git <verb>`, so only the old-string ACs cover them.

## 5. Findings

Severity: blocker, major, minor. Class (M6): blocking = affects correctness, consistency or a stated criterion; optional = preference or hypothetical.

### Cross-cutting

C-1. Negative-scope `git diff` checks are vacuous for untracked files. Severity: major for GITOWN (instance G2-1), minor elsewhere. Class: blocking.
 The user decision "track only the files each SPEC modifies" leaves the rest of the MoAI tree untracked (the worktree has no `.claude/rules`, `.claude/hooks` or `.moai/config`; confirmed by `ls`). `git diff --quiet|--name-only <base_sha>..HEAD -- <untracked path>` exits 0 / prints nothing whether or not the file was edited. Affected: GITOWN acceptance.md:50-53 (AC-006, spec-workflow.md) and :87 (`.claude/hooks .moai/config .claude/rules/moai`); REVGATE spec.md:141 (`.moai/config`, i.e. REQ-REVGATE-008 "not `workflow.yaml`"); ENV spec.md:132 (`.claude/hooks`); HOOKS REQ-HOOKS-008 "any other hook" (:84, no check). Tracked paths in the same bullets (`src tests tools packaging .github AGENTS.md`) are real checks.
 Fix: in §C step 1 record `sha256sum` of each protected untracked file (spec-workflow.md, workflow.yaml, the other hooks, git-strategy.yaml) in `progress.md` §E.2 and replace the `git diff` bullets with a `sha256sum -c`/`cmp` against that record.

C-2. Base-SHA contiguity. Severity: minor. Class: blocking.
 `git diff --name-only <base_sha>..HEAD ...` must list exactly each SPEC's own files (HOOKS :152, ENV :131, GITOWN acceptance.md:85, REVGATE :140), but only REVGATE declares an order (`depends_on`). If HOOKS/ENV/GITOWN run phases interleave on one branch, each diff also lists the others' files. Fix: state in each Conventions block that `base_sha` is taken immediately before the SPEC's first run edit and run phases are executed one at a time, or add a pathspec filter.

C-3. `moai update` scratch copy is not defined. Severity: minor. Class: blocking.
 "a scratch copy of the repository ... containing the N tracked files" (HOOKS :156, ENV :135, GITOWN acceptance.md:90, REVGATE :144) does not say how it is built. A bare directory may be refused or may be populated with the whole template set, so the `cmp` result could be an artifact. Fix: specify `cp -a` of the checkout (excluding `.git`, `.venv`) and record the file list created. (Verified: `CLAUDE_PROJECT_DIR` is not set in the Bash-tool environment, so the command cannot target the real project through it.)

### SPEC-HOOKS-001 (PASS-WITH-FIXES, minor only)

H2-1. AC-HOOKS-004 advisory re-run is ambiguous with the `env -u` convention. Severity: minor. Class: blocking (false failure).
 spec.md:135 says "the same command with `MOAI_SYNC_GATE_BLOCKING=0`", but the command is `env -u MOAI_SYNC_GATE_BLOCKING ... bash gate` (:131). Prefixing `MOAI_SYNC_GATE_BLOCKING=0` before `env` is cancelled by `-u`, the gate stays in blocking mode and the bullet fails. Fix: write the command as `env -u MOAI_SYNC_GATE_BLOCKING -u MOAI_AUTONOMY_TIER MOAI_SYNC_GATE_BLOCKING=0 CLAUDE_PROJECT_DIR=... bash ...` (assignment after the `-u` options).

H2-2. REQ-HOOKS-008 "any other hook" has no working check (C-1). Severity: minor. Class: blocking. Fix: hash record.

H2-3. Stale comment after the fix. Severity: minor. Class: optional. After deleting `status_line.sh:29-31`, the comment at `:26-28` ("Try the installed binary's own resolved path (captured at init/update time)") describes a branch that no longer exists. Add to plan task 5.

H2-4. AC-HOOKS-007 and AC-HOOKS-008 are measurements that cannot fail on substance (007 records, 008 allows a Gap). Severity: minor. Class: optional. Acceptable as stated; they consume 2 of 8 AC slots at the ceiling.

### SPEC-ENV-001 (PASS-WITH-FIXES, 2 major)

E2-1. AC-ENV-002 expected output is false. Severity: major. Class: blocking.
 spec.md:98-99 (and spec-compact.md AC-ENV-002 row) expects `grep -c -F 'command -v moai'` to print `<path>:1` for each of the three wrappers. Real counts (line counts): `handle-codex-review-gate.sh:2` (lines 69 and 70), `handle-multi-review-gate.sh:2`, `chain-event.sh:1`. The AC as written fails on the first two, and it is the precondition that gates the whole removal (plan.md:18, :39).
 Fix: expect "at least 1" (or use `grep -q` per file and require exit 0).

E2-2. `$LAUNCH_PATH` cannot be obtained by the stated runner, so the precondition is vacuous. Severity: major. Class: blocking.
 spec.md:87 defines `$LAUNCH_PATH` as the PATH of "the shell that launches Claude Code", recorded by the coordinator, but never says how. The coordinator is itself a Claude session: `printenv PATH` returns the 8-entry override literal; even `/proc/$CLAUDE_PID/environ` of this session returns the same 8 entries (this session is a daemon-spawned child, `claude bg-spare` under `claude daemon run`, not the user's interactive shell). `PATH="$LAUNCH_PATH" command -v moai` then finds `/home/rico/.local/bin/moai` because the literal contains it, so AC-ENV-002 passes even when the real launching shell lacks `~/.local/bin`, which is exactly the break E-2 warned about. The baseline in AC-ENV-004 (":108 equal to the literal means replace; a superset of `$LAUNCH_PATH` means merge") is likewise undecidable when `$LAUNCH_PATH` equals the literal.
 Fix: define `$LAUNCH_PATH` as supplied by the user from their interactive terminal (`printenv PATH`, recorded verbatim in `progress.md` §E.2 with that provenance), and start the AC-ENV-004/-005 sessions with an explicit `env PATH="$REPO/.venv/bin:$LAUNCH_PATH" claude -p ...` so the probe does not depend on the coordinator's own PATH.

E2-3. AC-ENV-005 fixture cannot be created as written. Severity: minor. Class: blocking.
 spec.md:115 writes `$SCRATCH/hookprobe/.claude/settings.json` from Python, but the Given does not create `$SCRATCH/hookprobe/.claude/` (FileNotFoundError). Fix: add `mkdir -p "$SCRATCH/hookprobe/.claude"`.

E2-4. AC-ENV-004 relies on an LLM reproducing Bash output (`claude -p "Use the Bash tool to run ... Print only the output."`). Severity: minor. Class: optional. Accept as Gap-eligible; prefer the hook probe (AC-ENV-005) as the deterministic evidence.

E2-5. Negative-scope bullet `git diff ... -- .claude/hooks` (spec.md:132) is vacuous for untracked hooks (C-1). Severity: minor. Class: blocking.

### SPEC-GITOWN-001 (PASS-WITH-FIXES, 1 major)

G2-1. AC-GITOWN-006 (the Frozen-file guard) cannot fail. Severity: major. Class: blocking.
 acceptance.md:50-53 runs `git diff --quiet <base_sha>..HEAD -- .claude/rules/moai/workflow/spec-workflow.md`. That file is untracked (`.claude/rules` is absent from the branch), so the command exits 0 regardless of edits. User decision 3 ("spec-workflow.md is NOT edited") therefore has no effective check; the same applies to the last bullet of AC-GITOWN-012 (:87) and to the Definition of Done line "byte-identical to `<base_sha>`" (:106). `AGENTS.md` (tracked) is a real check.
 Fix: record `sha256sum .claude/rules/moai/workflow/spec-workflow.md` (and the hooks/config paths) at §C step 1 in `progress.md` §E.2 and assert equality at the end.

G2-2. Inventory and plan file table omit three Scan S hits. Severity: minor. Class: blocking (reachability of AC-002/-004 from the plan).
 Scan S on the unchanged files also flags `manager-docs.md:8` ("NOT for: ... git branch management"), `run.md:165` ("... `git status`" in the evaluator note) and `plan/spec-assembly.md:336` (branch-creation prose), none listed in spec.md:44-76 or plan.md:55-67 (manager-docs lists only 76 and 95, run.md only 23, 37, 51, 152). An implementer following the table cannot reach "prints nothing". Fix: add the three lines to the inventory and table.

G2-3. Scan S limits. Severity: minor. Class: optional. See §4: non-imperative prose is flagged (forces prohibition rewrites), and the verb list is not exhaustive. Fix: add `show|ls-files|config|clone|init|restore|cherry-pick|remote|-C` for `git` and `api|run|release|repo|auth` for `gh`, or accept the limit explicitly.

G2-4. Stale progress statement. Severity: minor. Class: blocking (internal consistency). progress.md:10 says one item remains under "Open decisions for Kickoff Approval" but plan.md:105-107 records it as decided and "No open decisions remain". Fix: edit progress.md:10.

G2-5. Rule-layout claim is overstated. Severity: minor. Class: optional. spec.md:81 says each existing rule "carries YAML frontmatter"; always-loaded rules in this repo (`moai-constitution.md`, `goal-directive.md`, `main-checkout-branch-guard.md`) start with an H1 and have none. Harmless to the design (the new rule has no `paths:`), but the sentence is wrong.

G2-6. No size bound on the always-loaded rule, and residual executor routing elsewhere. Severity: minor. Class: optional. `.claude/rules/project/git-ownership.md` loads in every session; nothing caps it (suggest <= 40 lines). Files outside the 14 still describe `manager-git` as executing git (`e2e-tester.md:15` "git operations (manager-git)", `moai/SKILL.md:122,130,138,224`, `references/reference.md:24`); acceptable under the tracking decision, but the override rule could state that those references now mean proposal-only.

Checked and clear: AC-GITOWN-008's awk reads exactly the frontmatter and today counts the `Bash` and `bypassPermissions` lines (RED real); removing `Bash` from `manager-git` does not break another workflow, because every workflow that invokes it is in the edited set and its remaining output is text; the `main-checkout-branch-guard` hook that special-cases `manager-git` ships inert (`:95-100`) and is stricter, not broken, without `Bash`.

### SPEC-REVGATE-001 (FAIL)

R2-1. AC-REVGATE-004 cannot be satisfied, and the seeds are not tied to reviewer text. Severity: blocker. Class: blocking.
 spec.md:120 requires, for every entry whose source is a `file:line`, that `sed -n '<line>p' <file>` contains the match string. Plan §B:17 restricts seeds to lines in `handle-stop-goal.sh:64-66`, `status_line.sh:23`, `navigator-regen.sh:251`, `sync-phase-quality-gate.sh:391-399`, `settings.json:355`, `manager-git.md:4-5`, `spec-workflow.md:25-26`, and §F5 seeds the first six as `fixed-in`. `depends_on` (:15) and plan §C1 require HOOKS/ENV/GITOWN to be `completed` first, and those SPECs rewrite or delete exactly those lines (`exec` removed, PATH line deleted, description rewritten). The sed check then fails for every `fixed-in` seed. Separately, the match strings come from source code, not from the reviewer's finding text (which the author never saw, :29), so no entry demonstrates that it matches a real finding. This is the unresolved iteration-1 R-3.
 Fix: cite sources as text captured at `<base_sha>` (verified against a saved snapshot, or `git show <sha>:<path>` once tracked), and require match strings to be substrings of coordinator-supplied verbatim finding text saved in `progress.md` §E.2 (source `coordinator-supplied, §E.2 sample N`); drop any seed without such text.

R2-2. REQ-REVGATE-003 is conditional on a run-phase artifact and its AC can go green with the REQ unmet. Severity: major. Class: blocking.
 REQ-003 (:64) defers to `handler_shape` in `progress.md` §E.2, which does not exist yet. AC-REVGATE-003 Shape N (:112-113) passes on byte-identical pass-through while "REQ-REVGATE-003 cannot be met"; Shape T (:108-111) requires the match string to equal the whole reason text, yet spec.md:29 says finding sets differ run to run, so a stored whole-text entry would almost never match a later block (feature inert, AC green). Iteration-1 R-2 asked for the measurement at plan time; it was moved to the run phase.
 Fix: run plan §C step 3 now (one coordinator scratch run), then state REQ-003 for the observed shape only. If the shape is T or N, reword REQ-003 as pass-through plus policy document and drop the filter.

R2-3. REQ-REVGATE-005 has no AC for two of its three limbs. Severity: major. Class: blocking.
 REQ-005 (:70) covers "unavailable, times out, or returns no verdict". AC-REVGATE-005 (:122-128) tests only codex absent via the real binary (behavior of the unchanged Go handler, not the wrapper). Timeout and no-verdict are untested and the wrapper has no code path that identifies them. Fix: add stub-handler cases (stub prints nothing/exits non-zero, wrapper must exit 0 with no block) inside AC-REVGATE-005, and narrow the REQ to what the wrapper controls. No new REQ/AC needed (REVGATE is at the 8/8 ceiling).

R2-4. REQ-REVGATE-003 vs -007 wording conflict. Severity: minor. Class: blocking. -003 says the wrapper "shall let the block stand unchanged" (:64); -007 says it lets the block stand and "shall show the entry as informational text" (:76), which changes the output. Fix: "without suppressing it".

R2-5. Register file format leaves comments/header undefined. Severity: minor. Class: blocking. The AC-REVGATE-004 awk (:117) flags any line with `NF!=5`, so a header or `#` comment line fails, and REQ-004 does not forbid or define them. Fix: state "no header or comment lines", or have the awk skip `^#`.

R2-6. Per-workspace and host-specific content. Severity: minor. Class: optional. AC-REVGATE-001 measures only `$REPO` (plugin state is per workspace, coordinator worktree unchecked, :35), and REQ-REVGATE-001 has no repository artifact that enforces it. spec.md:84 hard-codes `/home/rico/.nvm/...` and `/home/rico/.claude/plugins/...` in a tracked SPEC, against the spirit of REQ-ENV-004.

R2-7. Register's active population is nearly empty by construction. Severity: minor. Class: optional. With the dependency SPECs completed first, all seeds for them are `fixed-in` (never suppress), leaving essentially one active entry (the `spec-workflow.md` Route A/B text). The register does not help the interim repetition it was introduced for (G3, :49). State this in the Context, or add genuinely `upstream-tracked` seeds once real finding text exists (R2-1).

R2-8. Negative-scope check for `workflow.yaml` is vacuous (C-1; spec.md:141). Severity: minor. Class: blocking.

## 6. Risk review: could any requirement break the user's session?

- ENV PATH removal: safe for this host (the launching environment for daemon-spawned sessions already equals the literal; `~/.bashrc` carries `~/.local/bin` for terminal launches), but the safety gate is AC-ENV-002 and it is vacuous as defined (E2-2). Side effect already documented (plan R2): where the launching shell loads nvm, `node` moves from v12 to v24 and the Codex plugin's node hooks start running.
- HOOKS D4 fix makes the sync gate's block enforceable (plan R2 documents it; 8-block cap noted).
- GITOWN: removing `Bash` and `bypassPermissions` from `manager-git` is safe (proposal-only text output); the new rule is small and path-unscoped by design.
- REVGATE: the filter fails in the safe direction (missing/malformed register or unmatched finding leaves the block standing, plan §F4); no session-breaking requirement found.

## 7. Minimal fix list, in order

1. REVGATE: R2-1 (sources/match strings from saved finding text and base-time snapshots), R2-2 (run §C step 3 now, restate REQ-003), R2-3 (stub cases for REQ-005).
2. ENV: E2-1 (>=1 instead of exactly 1), E2-2 (user-supplied `$LAUNCH_PATH`, explicit `env PATH=` for probes), E2-3 (mkdir).
3. GITOWN: G2-1 (sha256 record instead of `git diff` for untracked files), G2-2 (add three inventory lines), G2-4 (progress.md:10).
4. All four: C-1 (hash records for protected untracked files), C-2 (contiguous base_sha), C-3 (define the scratch copy).
5. HOOKS: H2-1 (env placement).

Re-audit (iteration 3) scope: R2-1..R2-3, E2-1..E2-3, G2-1, C-1..C-3, H2-1; if REVGATE's score stays under 0.75 the iteration-3 STOP/escalation rules apply.
