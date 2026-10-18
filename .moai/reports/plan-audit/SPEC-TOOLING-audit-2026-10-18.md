# Plan-phase audit: SPEC-HOOKS-001, SPEC-ENV-001, SPEC-GITOWN-001, SPEC-REVGATE-001

Date: 2026-10-18. Iteration: 1/3. Auditor: plan-auditor (read-only; no git/gh run, no SPEC or tooling file edited).
Reasoning context ignored per M1 Context Isolation. Format reference: SPEC-DEPS-001.
Cross-model audit (codex/glm/audit_multi): not invoked. No `audit_model` is configured in `.moai/config/sections/`, and the codex reviewer would re-run the very gate under study. `mcp__moai__spec_audit` returned `total_specs: 0` (it does not see these worktree specs), so it gave no evidence.

## 1. Verdicts

| SPEC | Formal verdict (M5 firewall) | Verdict on content once MP-7 is cleared | Approx. score (threshold) |
|---|---|---|---|
| SPEC-HOOKS-001 | FAIL (MP-7 only) | PASS-WITH-FIXES | 0.78 (Tier S 0.75) |
| SPEC-ENV-001 | FAIL (MP-7 only) | PASS-WITH-FIXES | 0.76 (Tier S 0.75) |
| SPEC-GITOWN-001 | FAIL (MP-7, tier mismatch) | FAIL (rework: tier, Frozen-zone dependency, ACs that cannot catch the defect) | 0.66 (Tier M 0.80) |
| SPEC-REVGATE-001 | FAIL (MP-7) | FAIL (rework: REQ-003..005 cannot be satisfied or tested as written) | 0.62 (Tier S 0.75) |

Must-pass results (per SPEC unless noted):
- MP-1 REQ numbering: PASS. HOOKS 001-008, ENV 001-007, GITOWN 001-007, REVGATE 001-008, no gaps or duplicates. AC ids are likewise sequential.
- MP-2 GEARS (judged on the REQ layer in spec.md section 2; the inline ACs are Given-When-Then, which is correct for Tier S): PASS. All REQs are event-driven, state-driven, ubiquitous or negative. Weak spots are listed as E-3 and X-8.
- MP-3 frontmatter: PASS. All 12 canonical fields plus `tier` are present and correctly typed (HOOKS/ENV/GITOWN/REVGATE spec.md:1-16). `related_specs` (HOOKS:15, ENV:15, GITOWN:15) is not a documented key (X-7).
- MP-4 language neutrality: N/A. The work is project-local to a Python repo. H-3 notes the hard-coded ruff paths.
- MP-5 D7: PASS, no BLOCKING finding. Every referenced SPEC id exists and is `draft`: HOOKS, ENV, GITOWN, REVGATE. `SPEC-GATE-001` (HOOKS spec.md:126) and `SPEC-NAVTEST-001/2/3` (HOOKS spec.md:118) are fixture literals, so the D7-5 "not found" SHOULD is a false positive.
- MP-6 D8: PASS (auto). The word `syscall` does not appear in any of the four.
- MP-7 clarification gate: **FAIL for all four.** `[NEEDS CLARIFICATION]` markers are open in plan.md: HOOKS 7 (plan.md:88-94), ENV 6 (plan.md:81-86), GITOWN 8 (plan.md:99-106), REVGATE 11 (plan.md:91-101). spec.md and progress.md carry none, so placement is correct, but the gate is score-independent. progress.md §E.1 of each SPEC nevertheless says `plan_status: audit-ready`, which contradicts "block run-phase entry until answered" (X-1).

## 2. Factual re-verification (focus item 1)

I re-read the primary-checkout files. All of the following match the SPEC text:
- `handle-stop-goal.sh`: pipeline `| exec` at 65, 70 and 75 (SPEC 64-66, 69-71, 74-76); `exit 0` at 79; `.moai/state/goal/${SESSION_ID}.json` fast path at 57-59. A grep across `.claude/hooks/moai/*.sh` confirms this is the only `| exec` in the tree.
- `handle-pre-tool.sh`: header comment at 16-21, `exit $?` tiers at 66-81.
- `.moai/status_line.sh`: mktemp at 7, trap at 8, comment at 20, `exec` at 23, 30, 35 and 40, hard-coded `/home/rico/.local/bin/moai` at 29-31. `settings.json:342` has `refreshInterval: 10`.
- `navigator-regen.sh`: `read` at 251, rows at 180, defaults at 178-179, `awk -F'\t'` at 212 and 237. The `read` versus `awk` collapse example in HOOKS spec.md:45 is consistent with bash IFS semantics. Sibling `navigator-audit.sh:522-582` uses the same `IFS=$'\t' read` idiom and is not mentioned (H-8).
- `sync-phase-quality-gate.sh`: Stop emission at 391-399 (blocking 393-394, advisory 396-397); comment 377-383; `run_step` 204-214; log line 402; python branch 228-241. The backup-versus-current diff is `230c230,240` only, so the D5 patch is present.
- `settings.json`: `env` 349-356, `PATH` at 355 with exactly 8 entries, the only `/home/` hit in the file. Stop array registers `handle-codex-review-gate.sh` at 144-149 with `timeout: 900`. No tokens or secrets found in the file (the only hits are `max_output_tokens` and `Read(./secrets/**)` deny rules), so tracking it exposes no secret.
- `workflow.yaml`: `codex:` 61, `review_gate:` 62, `enabled: true` 63, "Ships OFF" comment 56-60.
- `handle-codex-review-gate.sh`: 85 lines; tiers 62-74 with no `~/.local/bin`; fail-open 78-80; exit 0 at 82-85.
- `spec-workflow.md`: `[ZONE:Frozen] [HARD]` at 23; Route A at 25 and Route B at 26 are separate bullets after blank line 24.
- `git-strategy.yaml`: `mode: "personal"` 5, `push_to_remote: true` 48, `auto_commit: true` 61, `auto_pr`/`auto_push` false 62-63.
- Both `.gitignore` files (primary checkout and this worktree) lack `settings.local.json`. `/home/rico/.config/git/ignore:1` carries the rule. `settings.local.json` is 68 bytes, mode 0600, keys `enabledMcpjsonServers` and `teammateMode`.
- Plugin v1.0.6: block text at `stop-review-gate-hook.mjs:87`, `stopReviewGate` check at 154-157, block emit at 168-171, default false in `lib/state.mjs`, state dir absent, plugin enabled at `/home/rico/.claude/settings.json:7`.
- `claude --version` is 2.1.302; `moai` is 3.1.2.
- This session's own environment reproduces the ENV observation: PATH equals the 8-entry literal, `node` is `/usr/bin/node` v12.22.9, `ruff` is not found, `MOAI_CONFIG_SOURCE=sections`, `VIRTUAL_ENV` is empty. Both `~/.bashrc:118,121` and `~/.profile` prepend `~/.local/bin`.
- `/tmp` now holds 2062 `tmp.*` files and every one contains `transcript_path`. This is consistent with the 1.8k/1824 context figures, and the leak is still growing.

Not independently verifiable by me:
- Upstream issue #1827 (no network or gh allowed for this audit).
- D2 end-to-end reproduction, and D1/D2 re-runs. The sandbox guard refused script execution with a `HOME` override and refused compound `bash` invocations; this is the same limitation HOOKS plan.md R5 records. Static reading fully supports D1 and D2 (`exec` plus an EXIT trap is deterministic).

Mismatches found (all minor):
1. HOOKS plan.md:44 says the comments at `sync-phase-quality-gate.sh:13-23` and `:34-39` "assert the opposite" of the top-level form. They do not: line 15 (`{"decision":"block", ...}`) and line 35 (`{"decision":"block","reason":...,"systemMessage":...}`) document the top-level form. Only 377-383 and 387 assert the nested form. The script contradicts itself, and the SPEC missed that supporting evidence (H-5).
2. ENV E4 names only `handle-codex-review-gate.sh` as lacking a `~/.local/bin` tier. A scan shows `handle-multi-review-gate.sh` (registered in Stop at settings.json:152) and `chain-event.sh` also resolve `moai` without it (E-2).
3. GITOWN inventory is incomplete (G-3).
4. `/home/rico/.claude/jobs/fadbe668/tmp/sync-phase-quality-gate.sh.bak` is a job-tmp file the SPEC cites as the original, and it is the only copy of the original. It is not tracked or preserved anywhere, so HOOKS D5 "original behavior" depends on a temp path (optional).

## 3. Honesty review (focus item 2)

Most attribution is careful: HOOKS D1 "partial", D2 "yes", D3 "mechanism only", D4 "no", D5 "partial"; ENV "partial"; GITOWN "not applicable"; REVGATE "no". Overclaims or inconsistencies:
- REVGATE spec.md:28 states as fact "Those findings are the defects handled by SPEC-HOOKS-001, SPEC-ENV-001, and SPEC-GITOWN-001" and that the gate "ran at the end of at least four consecutive turns" with "169 passed tests ... each time". Spec.md:30 then says "The author did not see the gate's output". Only the repetition is attributed to the coordinator (R-5).
- The same second-hand provenance is stated flatly elsewhere: HOOKS spec.md:28 ("reported by the automated Codex review gate"), HOOKS spec.md:49 ("The Codex review gate reports that installed Claude Code 2.1.302 accepts ..."), ENV spec.md:28/46 ("reported by Codex"), GITOWN spec.md:30. All of these were relayed by the coordinator and never seen by the author. Each should say "as relayed by the coordinator" (X-9).
- HOOKS spec-compact.md:7 heads the defect list "Defects (reproduced by author)" although D4 is "no" and D1, D3, D5 are partial. Rename the heading (H-12).
- HOOKS spec.md:44 starts the D3 consequence with "Observed:" and then admits "derived by reading". Use "Derived by reading:".
- Stop schema, navigator end-to-end, `moai update` behavior and REVGATE repetition are all correctly labeled unverified in spec.md. No unverified item is stated as fact in a REQ or AC, except through the REQ/AC defects below.

## 4. Findings

Severity: blocker, major, minor. Class (M6): blocking = affects correctness, consistency or a stated criterion; optional = preference or hypothetical. "Required fix" is the minimal one.

### Cross-cutting (X)

X-1. Unresolved clarification gate (MP-7) in all four plan.md (HOOKS plan.md:88-94, ENV plan.md:81-86, GITOWN plan.md:99-106, REVGATE plan.md:91-101). Severity: blocker. Class: blocking.
 Many markers are not user decisions but measurements the run phase already schedules via an AC, so they cannot be "answered" before kickoff:
 - `moai update` preservation: HOOKS Q2, ENV Q2, GITOWN Q5, REVGATE Q8.
 - Origin of the PATH entry (ENV Q1) and replace-versus-merge (ENV Q6).
 - Evaluator exit codes (HOOKS Q1): measurable now by the coordinator.
 - Which gate fired (REVGATE Q6, Q7).
 Required fix: move measurement-type questions into plan §C pre-flight as tasks ("run X, record Y in progress.md"). Put only genuine user decisions through AskUserQuestion:
 - the single tracking scope (X-2);
 - the Frozen-zone edit (GITOWN Q3);
 - whether Astra is the MoAI orchestrator (GITOWN Q1);
 - the future of `manager-git` (GITOWN Q4);
 - the REVGATE disposition (REVGATE Q1) and register format;
 - the ruff fallback and the status-line path (HOOKS Q4, Q5, ENV Q5).
 Also change progress.md §E.1 `plan_status: audit-ready` until the markers are cleared.

X-2. Tracking scope is decided nowhere (circular). Severity: major. Class: blocking.
 HOOKS Q3 (plan.md:90), ENV Q3 (:83), GITOWN Q7 (:105) and REVGATE Q9 (:99) each say "must match the others". Every scope AC then contains an escape hatch: AC-HOOKS-006 spec.md:147, AC-HOOKS-008 :159, AC-ENV-007 :126, AC-GITOWN-008 :148 ("plus any file added by the recorded tracking-scope decision"). This makes the exact-scope checks unfalsifiable and lets an unreviewed file into the commit. `.claude/hooks/moai/` holds 43 scripts, 5 of which would be tracked, while a tracked `settings.json` registers about 15 of them.
 Required fix: the user decides once (recommend: track exactly each SPEC's own listed files). Write it into REQ-HOOKS-006/ENV-005/GITOWN-005/REVGATE-006 and delete the "plus any file added by the decision" clauses.

X-3. `.moai/status_line.sh:29-31` (`/home/rico/.local/bin/moai`) is orphaned between SPECs. Severity: major. Class: blocking.
 HOOKS tracks the file (REQ-HOOKS-006) but leaves the branch "as is" (plan.md:43) and defers it to ENV (Q4, plan.md:91). ENV excludes it as "owned by SPEC-HOOKS-001's scope" (spec.md:136) and defers it back (Q5, plan.md:85). The tracked file then contains an author home path, which is the exact condition REQ-ENV-004 forbids for `settings.json`.
 Required fix: assign it to HOOKS. Either extend REQ-HOOKS-002 with "and shall contain no absolute path under a user home directory" and remove branch 2 (branches 3 and 4 already cover `$HOME`-relative installs), or record it as accepted debt in HOOKS and delete ENV Q5.

X-4. The `moai update` recording ACs can record a false "not-listed". Severity: major. Class: blocking.
 Affected: AC-HOOKS-007 spec.md:149-153, AC-ENV-006 :117-121, AC-GITOWN-007 :139-143, AC-REVGATE-007 :122-126. The real `--yes` run happens "only if the dry run lists" the file, but `moai update --help` says `--dry-run` shows "planned archive and install operations", which may not enumerate template files. `--no-hooks` is correctly the git-hook flag. The AC also cannot fail on substance ("still met by the recording").
 Required fix: always run `moai update --templates-only --yes` in the scratch copy and derive preserved/merged/overwritten from `cmp` and diff, not from the dry-run listing. State whether it can touch user-level state outside the scratch directory, and run it with the user-level directories isolated or observed.

X-5. Several ACs invoke scripts that call git, or open live sessions, without saying who runs them. Severity: major. Class: blocking.
 The conventions (HOOKS spec.md:87 "Every step that runs `git`") cover only direct git, while AGENTS.md:13 also bars "scripts ... or other indirect methods". Affected:
 - AC-HOOKS-003 (`navigator-regen.sh` calls `git -C`);
 - AC-HOOKS-004/005 (the gate calls `git log`, `git diff`, `git rev-parse`);
 - AC-REVGATE-003/004 (real `moai` runs a codex review of uncommitted changes);
 - AC-ENV-003/004, AC-GITOWN-005 and AC-REVGATE-005 (live Claude sessions, network and quota).
 Required fix: add to each Conventions block "Every command in section 3 is run by the coordinator (Astra); implementers only edit files and report."

X-6. GITOWN tier mismatch: see G-1.

X-7. `related_specs` is not a documented frontmatter key (HOOKS spec.md:15, ENV :15, GITOWN :15; the schema lists `depends_on`, `lint.skip`, `bc_id`, `amendment_of`, `tier`, `issue_number`). Severity: minor. Class: optional. Fix: drop it (the relation is in prose) or use `depends_on` only where a real dependency exists.

X-8. Process-style REQs ("The observed treatment ... shall be recorded in progress.md": HOOKS-007, ENV-006, GITOWN-006, REVGATE-007) describe evidence collection, not product behavior. Severity: minor. Class: optional. Move to plan §E (Self-Verification) and keep the AC as a task; this also frees REQ budget.

X-9. Second-hand provenance written as direct report: see §3. Severity: minor (major for REVGATE: R-5). Class: blocking for REVGATE, optional elsewhere. Fix: say "as relayed by the coordinator".

X-10. Sequencing risk. Severity: minor. Class: optional. The MoAI gate is enabled now (`workflow.yaml:63`) and reviews uncommitted changes at every Stop. The three dependency SPECs' run phases leave exactly such changes uncommitted, so the repetition will recur during their own implementation. REVGATE lands last and its Q1(A) (disable the gate) is the only quick relief. Consider deciding Q1 first, or recording the expected noise and the 8-block cap (`hooks-system.md:213-215`) in the HOOKS/ENV/GITOWN plans.

### SPEC-HOOKS-001

H-1. REQ-HOOKS-004 / AC-HOOKS-004 are circular and self-attesting (spec.md:70-71, 124-132; plan.md:93 Q6). Severity: major. Class: blocking.
 The "correct" form is whatever the implementer writes as `stop_block_form` in progress.md. If `nested` is recorded, the AC passes with "the gate's emission lines unchanged", so no fix is needed to pass. The only enforcement evidence is a Gap by default. The author already has two independent sources for top-level (public hooks reference "Stop decision control"; the Codex plugin's own Stop hook at `stop-review-gate-hook.mjs:168-171`) plus the gate's own header at lines 15 and 35.
 Required fix: pin REQ-HOOKS-004 to top-level `decision` and `reason` (keep `systemMessage` at top level), drop the nested alternative from AC-HOOKS-004, and keep "enforced by 2.1.302" as an explicit live-test Gap.

H-2. REQ-HOOKS-001 mandates exit-status passthrough before Q1 asks whether it is desired (spec.md:62 versus plan.md:88). Severity: major. Class: blocking.
 Today the wrapper always exits 0 (`handle-stop-goal.sh:79`) and the evaluator status is discarded. Passing it through is a behavior change beyond "run once". Stderr is redirected to the log (lines 65, 70, 75), so an evaluator exit 2 (which `hooks-system.md:213` describes as blocking) would block Stop with no feedback text. If the goal engine blocks via exit 2, passthrough may newly hold turn-ends in armed-goal sessions.
 Required fix: before kickoff the coordinator measures the real evaluator's exit codes on an armed-goal fixture (the Q1 measurement). Then word REQ-001 either as "single dispatch, exit 0 preserved" or as "single dispatch, status passed through" with the stderr handling stated.

H-3. REQ-HOOKS-005 hard-codes `check src tests tools` (spec.md:74; code `sync-phase-quality-gate.sh:237`). Severity: major. Class: blocking.
 I confirmed `.venv/bin/ruff check --no-cache src nonexistent_dir` prints `E902 No such file or directory` and reports an error. In the gate, a non-zero C1 exit becomes a BLOCK by default (`:332-338`, mode blocking). A project without one of the three directories would hard-block its sync-phase Stop, where the old `ruff check .` was merely skipped. The hook is generic, shared multi-language template content.
 Required fix: pass only the existing directories among `src tests tools` (fallback `.`). State this in REQ-005 and add an AC row with a missing `tools/`. Also remove the fourth AC-HOOKS-005 bullet (spec.md:140), which lints the application, not the hook, and fails for unrelated lint regressions.

H-4. Fixture F1 uses `$SCRATCH` inside the stub (spec.md:89-97), but the conventions never say it is exported. Severity: minor. Class: blocking. A non-exported variable is invisible to the stub process, so `calls.log` assertions fail for the wrong reason. Fix: `export SCRATCH` in Conventions, or bake the absolute path into the stub.

H-5. Plan task 6 (plan.md:44) says the comments at `:13-23` and `:34-39` "assert the opposite". They document the top-level form (lines 15, 35). Only `:377-383` and `:387` say nested. Severity: minor. Class: blocking (it misdirects the edit). Fix: edit only 377-383 and 387, and cite the header lines as extra evidence in D4.

H-6. REQ-HOOKS-006 "byte-identical to the versions that pass AC-HOOKS-001 to AC-HOOKS-005" (spec.md:77) has no check. Severity: minor. Class: optional. Fix: drop the clause; AC-006 already tests tracked and clean.

H-7. D2/D1 "reproduced" claims could not be re-run by me (sandbox), though static reading confirms the mechanism. Severity: minor. Class: optional. The ACs correctly require a fresh RED run (plan.md §C step 4), which closes this at run time.

H-8. `navigator-audit.sh:522-582` uses the same tab-IFS `read` idiom; it is not listed as in or out of scope. Severity: minor. Class: optional. Fix: add one Out-of-Scope bullet.

H-9. The D4 fix turns a block that was effectively never enforced into one that is. With D5 live, a ruff failure at a sync commit will hard-block turn-end (once per commit, because the sentinel is written before the checks at `:178-186`). Severity: minor. Class: optional. Add a risk row to plan.md.

H-10. AC-HOOKS-004/005 do not clear `MOAI_SYNC_GATE_BLOCKING` and `MOAI_AUTONOMY_TIER` (gate `:345-373`). An ambient value flips the mode. Severity: minor. Class: optional. Fix: run the gate under `env -u MOAI_SYNC_GATE_BLOCKING -u MOAI_AUTONOMY_TIER`.

H-11. HOOKS spec-compact.md:7 heading "Defects (reproduced by author)" is wrong (see §3). Severity: minor. Class: optional.

### SPEC-ENV-001

E-1. REQ-ENV-002 (spec.md:65-66) asserts behavior of the Bash tool and "hook subprocesses", but AC-ENV-003 (spec.md:98-103) probes only the Bash tool. Severity: major. Class: blocking.
 The SPEC itself says "Whether hook processes see the same PATH was not observed" (spec.md:44). The REQ also describes third-party (Claude Code) behavior that the repository change cannot guarantee, and it rests on the unproven replace-versus-merge question (spec.md:45, Q6).
 Required fix: drop "and hook subprocesses" from the REQ, or add a probe (a throwaway hook that writes `printenv PATH` to a file).

E-2. REQ-ENV-001 removes PATH unconditionally while Q1 and Q4 (plan.md:81, 84) are open (spec.md:62-63). Severity: major. Class: blocking.
 If the author ever launches Claude from a launcher or non-login shell without `~/.local/bin`, `moai` resolution breaks silently for the three wrappers with no `$HOME/.local/bin` tier: `handle-codex-review-gate.sh`, `handle-multi-review-gate.sh`, `chain-event.sh`. The SPEC names only the first. Also, `~/.bashrc` sources nvm after the PATH exports, so node changes from v12 to v24 once the override is gone.
 Required fix: answer Q4 by recording the launching shell's PATH (plan §C step 2 already schedules this; make it a pre-kickoff measurement). Extend E4 and R1 to the three wrappers. Note in the SPEC that removing the override will make the Codex plugin's node hooks start running for real.

E-3. REQ-ENV-003 (spec.md:68-69) puts the obligation on the developer ("it shall be placed in ..."), which is not a system behavior. Severity: minor. Class: optional. Fix: "The repository's `.gitignore` shall exclude `.claude/settings.local.json` without relying on a global ignore file."

E-4. The AC-ENV-003 and the second bullet of AC-ENV-004 need live sessions; see X-5. They are correctly flagged as Gaps when no session is available. Severity: minor. Class: optional.

E-5. Positive checks: the AC-ENV-001 `diff ... | grep -c '^[<>]'` arithmetic (3) is correct. The AC-ENV-002 regex is valid against the real file (`/home/` appears only on line 355). Tracking `settings.json` exposes no secret (scanned).

### SPEC-GITOWN-001

G-1. Tier is wrong. Severity: major. Class: blocking.
 The SPEC edits 14 files (REQ-GITOWN-005, spec.md:89). `spec-workflow.md` § SPEC Complexity Tier defines Tier S as under 5 files, Tier M as 5-15 files with `acceptance.md`, and a 0.80 PASS threshold. `tier: S` is at spec.md:14.
 Required fix: set `tier: M` and add acceptance.md, or split into two Tier S SPECs (agents, and workflows plus rule plus CLAUDE.md), each under 5 files.

G-2. Requirements depend on an unanswered Frozen-zone question and contradict the plan constraint. Severity: major. Class: blocking.
 REQ-GITOWN-002/005 and AC-002/006/008 require editing `spec-workflow.md` (the `[ZONE:Frozen] [HARD]` paragraph at 23, Route bullets at 25-26). Plan R2 (plan.md:74) says "do not edit spec-workflow.md until [Q3] answered". If Q3 is "no", the REQs, the "14 files" count, and AC-002/006/008 become unsatisfiable. I could not find any enforcement text for Frozen on local edits in the files I read.
 Required fix: resolve Q3 via AskUserQuestion before approval. If "no", remove `spec-workflow.md` from REQ-002 and the edited set, make the override a separate rule file, and change "14" to "13".

G-3. ACs cannot catch the defect they target, and the inventory is incomplete. Severity: major. Class: blocking.
 AC-GITOWN-001/002 pass if the phrase "proposed repository action" is present and about 14 listed strings are gone. REQ-001 says the agent "shall not direct it to execute". Imperative Git text I confirmed outside the cited lines would survive:
 - `manager-git.md:96, 119-120, 127, 160-162` (`git checkout main && git pull`, `git fetch origin`);
 - `manager-develop.md:81` (`| Git operations | manager-git |`);
 - `sync/delivery.md:213-330` (Step 3.2: `git push -u origin`, `gh pr create`, `gh pr merge`, `gh pr ready`, checkouts);
 - `plan/spec-assembly.md:281, 312-314` (`gh issue create`, `gh issue comment`);
 - `spec-workflow.md:34-36, 51, 62` (Route A "commits + pushes directly to `main`").
 Required fix: add a negative AC per file. A grep for `\b(git|gh) (push|commit|add|checkout|switch|fetch|pull|merge|branch|worktree|tag|pr|issue)\b` must return only lines inside a block labeled "Proposed repository action", with the hit list recorded. Extend the inventory with the lines above.

G-4. REQ-GITOWN-004's second clause has no AC. Severity: major. Class: blocking.
 "shall not introduce any carve-out that lets a sub-agent run git or gh" (spec.md:86) is covered only by AC-GITOWN-004 (AGENTS.md unmodified, spec.md:122-125). An edit saying "manager-git may run read-only `git status`" passes every AC. Fix: extend the AC-GITOWN-005 probe with a request such as "run git status" that must be declined, and add a grep for permission phrases (`may run`, `read-only`, `exception`) in the 12 edited prose files.

G-5. REQ-GITOWN-003 hard-codes the persona "Astra" and an exact sentence in MoAI-managed agent files (spec.md:83), while Q1 (plan.md:99) asks whether Astra is the MoAI orchestrator. Severity: minor. Class: blocking (resolve with X-1). `manager-lead` (which carries the `Agent` tool) may itself be a coordinator in some flows.

G-6. AC-GITOWN-005 (spec.md:127-132) relies on one LLM run. Severity: minor. Class: optional. Require at least 3 trials, and make the scratch repo have no remote and no `gh` auth because `manager-git` still holds `Bash` and `bypassPermissions` (agent lines 8, 12).

G-7. "Inside the Frozen paragraph" (plan.md:66) is not established: line 24 is blank and 25-26 are separate bullets. Severity: minor. Class: optional. Verify the marker scope or reword.

G-8. Inventory line numbers I checked are accurate (manager-git 4, 5, 8, 12, 31-32, 99-114, 125, 156, 168-170; manager-develop 50, 52, 138, 165-169, 185, 187; manager-docs 76, 95; manager-spec 55, 200; manager-lead 216; workflow lines; CLAUDE.md:53; `git-strategy.yaml`). Every AC "old string" exists verbatim in the file (for example `task-decomposition.md:294` "no separate agent spawn for git operations").

### SPEC-REVGATE-001

R-1. AC-REVGATE-004 contradicts the reference host (spec.md:104-109). Severity: major. Class: blocking.
 It runs with `PATH="$HOME/.local/bin:/usr/bin:/bin"` and says "no `codex` executable on PATH", but the SPEC itself (spec.md:35) and I confirm `codex` is at `/home/rico/.local/bin/codex`, the same directory that holds `moai`. The test would run the real reviewer. `$SCRATCH/gate` is also not a git repo, so "review uncommitted changes" is undefined there.
 Required fix: build a scratch `bin/` containing only a symlink to `moai`, run with that PATH, and make the scratch a git repo (coordinator-created).

R-2. REQ-REVGATE-003/004 and AC-REVGATE-003 are not implementable or testable until plan §C step 3 runs. Severity: major. Class: blocking.
 The ACs reference "the shape recorded in progress.md" (spec.md:97-99), "the register's recorded format" (:102), and decisions not yet made (`retained_gate`, `register_path`, `policy_doc_path`, :82). The wrapper header (`handle-codex-review-gate.sh:9-12`) says the handler blocks "on a fail verdict". REQ-003 ("at least one finding that is not recorded ... shall block") could widen blocking to pass-verdicts that list findings. The plan admits pure-shell splitting may be impossible (R1, plan.md:63) and then falls back to option (A), which makes REQ-003..005 vacuous. Half of the plan's own branches cannot satisfy the REQs.
 Required fix: run §C step 3 and Q1 now (plan phase, coordinator, one scratch run). Then state the REQs against the captured shape, or split the register into a separate SPEC after the shape is known.

R-3. Seed entries cannot satisfy REQ-REVGATE-004 (spec.md:65-66). Severity: major. Class: blocking.
 A "literal match string that appears in the finding text" is required for findings the author never saw (spec.md:30), and plan task 6 (plan.md:45) seeds them from SPEC prose. Fix: the coordinator supplies the verbatim text of the repeated gate outputs (at least four turns) in plan §C. Match strings are copied from them, and AC-003 verifies each against the quoted text.

R-4. `fixed-in` acknowledgements demote a regression to advisory (spec.md:66, plan.md:45). Severity: major. Class: blocking.
 This contradicts the plan's own anti-pattern ("Do not make an acknowledgement mean always allow", plan.md:76) and R2/R7. Once a defect is fixed, a recurrence is a genuine new finding. Fix: only `upstream-tracked` and `accepted` entries suppress. `fixed-in` entries are informational or are auto-removed (answer Q11 in the SPEC).

R-5. Overclaim at spec.md:28 versus 30 (see §3). Severity: major. Class: blocking. Fix: "reportedly".

R-6. REQ-REVGATE-005 and REQ-REVGATE-003 are unsatisfiable when the plugin gate is retained. Severity: major. Class: blocking.
 REQ-001 and AC-001 allow either gate to be retained. The plugin gate blocks on timeout, failure, empty output and unexpected answers (spec.md:34, `stop-review-gate-hook.mjs:69-96,112-139`), which contradicts REQ-005. The register filter cannot live in the plugin, which REQ-008 and Out-of-Scope forbid changing. Fix: scope REQ-003/004/005 to the MoAI gate, and restrict `retained_gate` to `moai` or `none`, or add a plugin-side handling REQ.

R-7. AC-REVGATE-008 second bullet (spec.md:132) tests "repetition stops", for which no REQ exists, and mixes it with the scope check. Severity: minor. Class: optional. Fix: add a REQ or move the observation to plan §E as a non-gating note.

R-8. REQ-REVGATE-006 tracks the whole `workflow.yaml` (spec.md:71-72) while the other ~30 `.moai/config/sections/*.yaml` files stay untracked. The binary reads the whole directory (`MOAI_CONFIG_SOURCE=sections`). Severity: minor. Class: optional. Part of X-2.

R-9. AC-REVGATE-002 (spec.md:90-94) will cite user-level files (`/home/rico/.claude/settings.json:7`, plugin cache paths) in a tracked document, against the spirit of REQ-ENV-004. Severity: minor. Class: optional. Fix: cite `~/.claude/settings.json` (or `$HOME`).

R-10. Sequencing: see X-10. `depends_on` (REVGATE frontmatter) is a hard dependency, yet plan §C step 1 (plan.md:19) allows proceeding with dependencies open. Severity: minor. Class: optional. Fix: pick one.

## 5. Risk review (focus item 5)

Requirements that would break a user session if implemented as written:
- H-2 (exit passthrough with stderr sent to a log could block Stop with no message, or newly hold armed-goal sessions).
- H-3 (a missing `tools/` directory makes the gate hard-block).
- E-2 (removing PATH before the launch shell is known; three wrappers silently lose `moai`).
- R-4 (silences regressions).
- X-3 (home path is shipped in a tracked file).

Checked and clear:
- No secrets in `settings.json`, `workflow.yaml` or `settings.local.json` content. `settings.local.json` is not tracked, and ENV adds the ignore rule.
- Removing PATH does not remove anything node needs: node v24 is already provided by the launching shell via nvm in `~/.bashrc`, while the override currently forces v12.
- Fail-open versus fail-closed for the status line and the stop-goal wrapper is unchanged in direction.

## 6. Minimal fix list, in order

1. Clear MP-7 in all four plan.md files: convert measurements to plan §C tasks, ask the user the true decisions via AskUserQuestion, and set `plan_status` accordingly (X-1).
2. Make the single tracking-scope decision and delete the "plus any file added" clauses (X-2). Resolve the status-line path ownership (X-3).
3. Add "coordinator runs every command in section 3" to all four Conventions (X-5). Make the `moai update` ACs always do the real scratch run and decide from `cmp` (X-4).
4. HOOKS: pin D4 to top-level (H-1), resolve Q1 by measurement and reword REQ-001 (H-2), make ruff paths conditional (H-3), export `SCRATCH` (H-4), fix the plan.md:44 wording (H-5).
5. ENV: remove the hook clause from REQ-ENV-002 or add a probe (E-1), answer Q4 and extend the wrapper list (E-2).
6. GITOWN: tier M or split (G-1), settle the Frozen-zone question (G-2), add negative and probe ACs and complete the inventory (G-3, G-4).
7. REVGATE: run §C step 3 and Q1 now (R-2), supply real finding text (R-3), drop `fixed-in` suppression (R-4), fix the AC-004 PATH (R-1), restrict REQ-003..005 to the MoAI gate (R-6), reword the provenance sentence (R-5).

Re-audit (iteration 2) should be scoped to this defect delta: X-1 to X-5, H-1 to H-5, E-1 and E-2, G-1 to G-4, R-1 to R-6.
