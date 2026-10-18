# Plan-phase re-audit (iteration 3/3, final): SPEC-HOOKS-001, SPEC-ENV-001, SPEC-GITOWN-001, SPEC-REVGATE-001

Date: 2026-10-18. Auditor: plan-auditor (read-only; no git/gh run, no SPEC or tooling file edited, no agent spawned).
Reasoning context ignored per M1 Context Isolation. The four user decisions passed in the prompt were treated as fixed. `progress.md` dispositions were not trusted; every fix was re-read in the SPEC text and, where a command is involved, executed on this host (read-only, stdin-only).
Cross-model audit (codex/glm/audit_multi): not invoked (no `audit_model` configured).
Scope: iteration-2 delta (R2-1..R2-8, E2-1..E2-3, G2-1..G2-6, H2-1..H2-3, C-1..C-3) plus a regression sweep of the iteration-3 edits.

## 1. Verdicts

| SPEC | Tier / threshold | Score (iter2 -> iter3) | Verdict | Open findings | Ready for Kickoff Approval |
|---|---|---|---|---|---|
| SPEC-HOOKS-001 | S / 0.75 | 0.90 -> 0.93 | PASS-WITH-FIXES (minor only) | 3 minor | yes |
| SPEC-ENV-001 | S / 0.75 | 0.84 -> 0.88 | PASS-WITH-FIXES (minor only) | 4 minor | yes |
| SPEC-GITOWN-001 | M / 0.80 | 0.83 -> 0.91 | PASS-WITH-FIXES (minor only) | 3 minor | yes |
| SPEC-REVGATE-001 | S / 0.75 | 0.69 -> 0.82 | PASS-WITH-FIXES (2 major, one-line fixes) | 2 major, 4 minor | no |

No score regressed against iteration 2, so the STOP-on-regression rule is not triggered. No blocker remains in any SPEC (R2-1 is resolved).
Category scores (Clarity / Completeness / Testability / Traceability): HOOKS 0.92 / 1.00 / 0.88 / 1.00; ENV 0.88 / 1.00 / 0.80 / 1.00; GITOWN 0.90 / 0.95 / 0.90 / 1.00; REVGATE 0.88 / 0.95 / 0.70 / 0.95.
Iteration cap: this is iteration 3 of 3. Per the Retry Loop Contract the orchestrator escalates to the user. Recommended option: PASS-with-debt for HOOKS, ENV, GITOWN (minor only); for REVGATE either option 1 with R3-1 and R3-2 recorded as debt, or an explicit user-approved extension to apply the two one-line fixes. Verdict authority stays with this report; an orchestrator self-check does not replace it.

## 2. Must-pass results

- MP-1 REQ numbering: PASS. HOOKS REQ-001..008 (spec.md:63-85), ENV 001..006 (:67-83), GITOWN 001..007 (spec.md:91-110), REVGATE 001..008 (:64-86); AC numbering likewise contiguous (HOOKS 001..008, ENV 001..008, GITOWN 001..013 in acceptance.md, REVGATE 001..008). Counts vs ceilings (spec-workflow.md:146-152, REQ and AC counted independently): HOOKS 8/8 REQ, 8/8 AC; ENV 6/8, 8/8; GITOWN 7/16, 13/16; REVGATE 8/8, 8/8. No ceiling exceeded. HOOKS, ENV, REVGATE have zero AC headroom, so any fix below must be added as a bullet inside an existing AC.
- MP-2 GEARS (judged on the REQ layer in spec.md; ACs are Given-When-Then, correct for the verification layer): PASS. Every REQ is event-driven, state-driven, Where, ubiquitous or negative. Only blemish: REQ-REVGATE-003 ends with a definitional second sentence without `shall` (spec.md:71, "A finding is matched when ..."); optional.
- MP-3 frontmatter: PASS. All 12 canonical fields plus `tier` present and typed correctly in all four (spec.md:1-15, REVGATE :1-16). Version quoted ("0.3.0"), dates ISO, `phase: "v0.1.1 target"` is a release label (not a prohibited stage name), no rejected snake_case alias. REVGATE `depends_on` (:15) is a documented optional key (spec-frontmatter-schema.md:148).
- MP-4: N/A (project-local Python repository).
- MP-5 D7: PASS. Referenced IDs: HOOKS/ENV/GITOWN/REVGATE (all `status: draft`), plus `SPEC-GATE-001` and `SPEC-NAVTEST-001/2/3`, which are fixture literals (HOOKS spec.md:123,133), not references. No retired/superseded/archived reference.
- MP-6 D8: PASS (auto). `grep -c syscall` over all artifacts of all four SPECs: zero.
- MP-7 clarification gate: PASS. `grep -rn 'NEEDS CLARIFICATION'` over every file of the four directories (spec, plan, acceptance, spec-compact, progress, observed-gate-output): zero hits. A case-insensitive `clarification` search finds only the lowercase prose "all clarification markers removed" in HOOKS/ENV/GITOWN progress.md:10, which is not a `[NEEDS CLARIFICATION: topic]` marker and sits outside plan.md/research.md.

## 3. Verification of the iteration-2 delta (from the text)

### REVGATE
- R2-1 (blocker): RESOLVED. Register seeds are now one per distinct title in `observed-gate-output.md` (plan.md:60-73); AC-REVGATE-004 (spec.md:119-125) verifies each entry's evidence field against that file instead of `sed -n` on source lines that the dependency SPECs rewrite. I compared every seed (title, path, sample, item number) with the observed file verbatim: A1 "Keep Git operations with Astra" / manager-git.md; A2 "Exit after invoking the resolved goal-hook binary"; A3 "Remove the machine-specific shared PATH override"; A4 "Preserve empty columns when reading navigator rows"; A5 "Allow the status-line temporary-file cleanup to run"; B1 "Exit after dispatching the goal hook"; B2 "Emit the Stop decision at the top level"; B3 "Run Ruff from the project virtual environment"; B4 "Preserve empty fields when reading navigator rows"; B5 "Allow status-line cleanup to run after MoAI exits". All ten match, 10 distinct titles (5 + 5), item numbers correct, paths correct. The plan-time source snapshot in progress.md:19-26 matches the observed ranges (`22-24`, `251-252`, `381-384`, `228-230`, `4-5`, `64-66`, `355`).
- R2-2 (major): RESOLVED. Shape T/N branches and the run-phase `handler_shape` dependency are gone; REQ-003 is stated for the observed shape with identity = normalized title + path, line ranges ignored (spec.md:71, G3 :49-52); AC-REVGATE-003 tests a shifted range (:114). Residual: R3-4.
- R2-3 (major): RESOLVED. AC-REVGATE-005 (:127-133) adds stub cases (a) silent exit 0, (b) silent exit 124, (c) `not json`, plus no-`moai` and the real-binary Gap-eligible bullet; REQ-005 (:77) is narrowed to what the wrapper controls. Consistent with the wrapper (`handle-codex-review-gate.sh:82-85`, always `exit 0`, no `set -e`).
- R2-4: RESOLVED (REQ-003 "allow the stop and show ... advisory" vs REQ-007 "byte-identical", :71, :83; no conflict). R2-5: RESOLVED (six fields, "no header or comment lines", :74, awk :121). R2-6: RESOLVED (AC-REVGATE-001 runs per workspace root :98-100; `$NODE`/`$CODEX_COMPANION` moved to progress; only residual `/home/` text is context at :32). R2-7: RESOLVED (G4 states the active population is empty at seed time, :54-56). R2-8: RESOLVED by the sha256 record (:93, :147).

### ENV
- E2-1: RESOLVED. AC-ENV-002 (spec.md:103) expects N >= 1 per wrapper; real counts on this host: handle-codex-review-gate.sh 2, handle-multi-review-gate.sh 2, chain-event.sh 1 (matches the quoted "2, 2, and 1").
- E2-2: RESOLVED. `$LAUNCH_PATH` is user-supplied with recorded provenance (:89); AC-ENV-004/-005 launch under an explicit `env PATH="$REPO/.venv/bin:$LAUNCH_PATH"` (:112-113, :120), so replace-versus-merge is decidable (baseline first entry `/home/rico/.local/bin` vs `$REPO/.venv/bin`); missing value makes the ACs Gaps. Residual: R3-8.
- E2-3: RESOLVED (`mkdir -p "$SCRATCH/hookprobe/.claude"`, :119; `REPO` exported).
- AC-ENV-001 expected `3` verified by reasoning against settings.json:354-356 (two `<` lines for NO_FLICKER-with-comma and PATH, one `>` line).

### GITOWN
- G2-1: RESOLVED. AC-GITOWN-006 (acceptance.md:53-56) and the last bullet of AC-GITOWN-012 (:90) use `sha256sum -c` on a record that includes every `.claude/rules/moai/` file (so `spec-workflow.md`); a changed file makes `sha256sum -c` print FAILED and exit non-zero (I confirmed it fails closed on an empty/mismatched record). AGENTS.md keeps a real `git diff` check (tracked).
- G2-2: RESOLVED. Inventory adds `manager-docs.md:8`, `run.md:165`, `plan/spec-assembly.md:336` (spec.md:56, :67, :73); plan file table rows now list 8, 165 and 336 (plan.md:57, :60, :64).
- G2-3: RESOLVED. Extended verb list at acceptance.md:15. I ran the extended-verb regex over all 13 files: zero hits for `repo|config|init|show|remote|api|auth|release|run|clone|restore|ls-files|cherry-pick|-C`, so no new false positives; the scan, run (mawk) on three of the files, still prints 9 hits, so the RED baseline is real.
- G2-4: RESOLVED (progress.md:10 now says decided). G2-5: RESOLVED in spec.md:83 (residual: plan.md:7, R3-9). G2-6: RESOLVED (REQ-GITOWN-003 caps the rule at 40 lines and states other `manager-git` references mean proposal-only, spec.md:98; AC-GITOWN-005 checks `wc -l` <= 40 and `proposal-only`, acceptance.md:50).

### HOOKS
- H2-1: RESOLVED. I executed `FOO=1 env -u FOO -u BAR FOO=0 printenv FOO` which prints `0`, so an assignment written after the `-u` options survives; AC-HOOKS-004 (spec.md:138) and the Conventions bullet (:92) use that form. H2-2: RESOLVED (sha256 record, :93, :157). H2-3: RESOLVED (plan.md:46 deletes the `:26-28` comment). H2-4: accepted as stated.

### Cross-cutting
- C-1 (sha256 replaces `git diff` on untracked paths): RESOLVED in logic for every affected AC: HOOKS AC-006 last bullet (:157), ENV AC-007 last bullet (:136), GITOWN AC-006/-012 (acceptance.md:53-56, :90), REVGATE AC-007 last bullet (:147). Each would fail if a recorded file changed, and each is runnable by the coordinator (no git; `sha256sum` only). Tracked paths keep real `git diff` checks. Residuals: R3-7 (path format), R3-8 (ENV binary).
- C-2 (contiguous `base_sha`): RESOLVED in all four Conventions (HOOKS :90, ENV :88, GITOWN acceptance.md:7, REVGATE :91) and in each plan §C.
- C-3 (scratch copy): RESOLVED. Identical `tar ... --exclude=.git --exclude=.venv` recipe plus before/after file list in all four (HOOKS :94, ENV :91, GITOWN acceptance.md:11, REVGATE :94). Residual: R3-10 (optional).

## 4. Regression sweep: new defects introduced by the iteration-3 edits

- File-set double ownership across the four SPECs: none in the tracked sets. HOOKS = 4 hook/script files; ENV = `.claude/settings.json` + `.gitignore`; GITOWN = 14 files; REVGATE = wrapper + policy + register. Disjoint. Residual overlap only through the conditional sync-phase notes (R3-9b).
- Register evidence vs observed-gate-output.md: all ten seeds verbatim-consistent (section 3). The tracker column in the plan table says "issue #1827" while AC-REVGATE-004 greps the full URL; plan.md:73 gives the `+`-joined URL convention, so it is resolvable (not a finding).
- Unrunnable / unfalsifiable ACs found: R3-1 (unrunnable on this host), R3-2 (REQ-007 not falsifiable for a partially parseable block). Others: see minors.
- Tier ceilings: no breach (MP-1).
- MP-7 and frontmatter: clean (section 2).

## 5. Findings

Severity: blocker / major / minor. Class (M6): blocking = affects correctness, internal consistency or a stated criterion; optional = preference.

### SPEC-REVGATE-001 (PASS-WITH-FIXES, 2 major)

R3-1. AC-REVGATE-004 awk cannot pass on this host. Severity: major. Class: blocking.
 spec.md:121 uses interval expressions `^[0-9]{4}-[0-9]{2}-[0-9]{2}$` inside `awk`. `awk` here is `/usr/bin/mawk` (`readlink -f $(command -v awk)`), and a test `echo 2026-10-18 | awk '$1~/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/ {print "ok"}'` prints nothing, while the same pattern written with `[0-9][0-9][0-9][0-9]-...` matches. Result: the `$5!~/.../` clause is true for every line, so the awk prints every register line and the "prints nothing" condition (:122) fails for a perfectly valid register (false failure; wrapper itself uses only mawk-safe constructs).
 Fix: replace the pattern with `^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$` (mawk and gawk safe). This is the only interval expression in the four SPECs' awk commands (searched).

R3-2. The central safety property is not falsifiable for a partially parseable block. Severity: major. Class: blocking.
 REQ-REVGATE-007 (:83) and plan §F4 (plan.md:53) require byte-identical output when any finding is unmatched or the output is unparseable. AC-REVGATE-003 (:113-117) tests only well-formed bullets: one entry, reworded title, empty/missing/malformed register, `fixed-in`. A parser that extracts the well-formed bullets and silently ignores any other bullet (or treats a block with zero extracted bullets as "all matched", a vacuous truth) passes every AC while hiding a real finding.
 Fix (a bullet inside AC-REVGATE-003, no new AC): "And with X and Y both active and a third bullet that does not match the observed format (for example `- [P1] No location given`), and with a block whose reason text has no bullet lines, `cmp` reports identical."

R3-3. Register title form is ambiguous. Severity: minor. Class: blocking.
 plan.md:60-71 headings "Title (as printed)" but REQ-003 (spec.md:71) matches the finding's normalized (lower-case) title against "the entry's title", AC-REVGATE-003 uses `title x one` (:113), and AC-REVGATE-004 (:124) requires the sample item's normalized title to equal the entry's title. Seeds written as printed ("Keep Git operations with Astra") would fail AC-004.
 Fix: state in REQ-REVGATE-004 that the title field stores the normalized form, and list the normalized strings in the seed table.

R3-4. AC-REVGATE-003 step 0 depends on a nondeterministic live reviewer. Severity: minor. Class: blocking (false failure).
 spec.md:110 fails the SPEC if the shape differs, and requires at least one bullet from a real reviewer run on "one obvious defect"; a reviewer that returns ALLOW produces no block to inspect and the outcome is undefined. Fix: "if the reviewer returns no block, retry with a different defect up to 3 times; if still none, report a Gap, not a failure".

R3-5. The malformed-register case can pass trivially. Severity: minor. Class: blocking.
 spec.md:116 "an ACK with one malformed line (five fields)" does not require X and Y to be present as valid active entries; with only the malformed line nothing matches and `cmp` is identical for the wrong reason. Fix: "X and Y active plus one five-field line".

R3-6. AC-REVGATE-002 knob citations. Severity: minor. Class: blocking.
 :106 requires `sed -n '<line>p' <file>` for each cited `file:line`, while the knob list cites ranges (`settings.json:144-149`, spec.md:41). `sed -n '144-149p'` is invalid. Also the first command (:104) needs the file tracked, so AC-002 only passes after the commit in plan §F7, while plan §E.2 says to run ACs in §F order. Fix: require single-line citations and state that AC-002 runs after the commit.

### SPEC-ENV-001 (PASS-WITH-FIXES, minor only)

R3-7. (all four) `protected.sha256` path format is unspecified. Severity: minor. Class: optional.
 HOOKS :93, ENV :90, GITOWN acceptance.md:10, REVGATE :93: "in `sha256sum` format ... write those lines to `$SCRATCH/protected.sha256` and run `sha256sum -c`". With relative paths the check depends on the cwd and reports FAILED to open (fails closed, so safe, but confusing). Fix: record absolute paths, or say "run from `$REPO`".

R3-8. ENV: REQ-ENV-006 names the `moai` binary but no check covers it. Severity: minor. Class: blocking (stated criterion without a check).
 spec.md:83 forbids changing "any hook script, or the `moai` binary"; the record (:90) and AC-ENV-007 (:136) hash only the hooks and `settings.local.json`. Fix: add the `moai` binary to the `protected_sha256:` list.

R3-8b. ENV probes under `claude -p`. Severity: minor. Class: optional.
 AC-ENV-004 (:113) asks the model to use the Bash tool in non-interactive mode; permission to run Bash may be denied without `--allowedTools Bash`. The SPEC already treats it as Gap-eligible and names AC-ENV-005 as the deterministic evidence. Also `$SCRATCH/settings.before.json` (:88) is described as saved "in progress.md"; say that the file is copied into `$SCRATCH` and its content recorded in progress.md.

### SPEC-GITOWN-001 (PASS-WITH-FIXES, minor only)

R3-9. Stale text. Severity: minor. Class: blocking (internal consistency).
 acceptance.md:3 says "Verification layer for `spec.md` v0.2.0" (spec is 0.3.0); plan.md:7 still says existing rules carry "YAML frontmatter and `paths:` globs", contradicting the corrected spec.md:83 (always-loaded rules have none). Fix: one-word edits.

R3-9b. (HOOKS, ENV, GITOWN) Sync-phase follow-up tasks conflict with the scope REQs. Severity: minor. Class: blocking.
 HOOKS plan.md:49 (`.moai/project/structure.md`), ENV plan.md:45 (`tech.md`), GITOWN plan.md:49 (`tech.md` or `structure.md`) edit tracked files outside the sets named by REQ-HOOKS-008 (spec.md:85), REQ-ENV-006 (:83), REQ-GITOWN-007 (:110), and three SPECs may edit the same two files. The AC diffs are taken at the run-phase commit, so the ACs still hold. Fix: add "except the conditional sync-phase documentation note in `.moai/project/*.md`" to the three REQs, or delete the follow-up tasks.

### SPEC-HOOKS-001 (PASS-WITH-FIXES, minor only)

No finding unique to HOOKS beyond R3-7 and R3-9b; AC-HOOKS-004 `env` placement verified by execution. Note: REQ/AC are at the 8/8 ceiling.

R3-10. (all four, optional) The scratch copy of the primary checkout includes `.claude/worktrees` (full copies of other worktrees). Fix: add `--exclude=.claude/worktrees`.

## 6. Risk review

- ENV PATH removal: the gate that protects it (AC-ENV-002 + user-supplied `$LAUNCH_PATH`) is now meaningful; the node v12 -> v24 side effect is documented (plan R2).
- GITOWN: removing `Bash`/`bypassPermissions` from `manager-git` stays safe; the always-loaded override rule is now capped at 40 lines.
- REVGATE: the register is empty-by-construction at seed time and says so (G4); the filter fails in the safe direction, but R3-2 means that direction is not yet proven by an AC.
- No requirement in any of the four can break the user's session on its own.

## 7. Minimal fix list (final)

1. REVGATE: R3-1 (mawk-safe date regex), R3-2 (partial-parse bullet in AC-003); then R3-3..R3-6.
2. ENV: R3-8 (hash the `moai` binary).
3. GITOWN: R3-9 (two stale strings).
4. All: R3-7, R3-9b, R3-10 (optional).
