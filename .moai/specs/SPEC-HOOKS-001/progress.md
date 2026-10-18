# SPEC-HOOKS-001 — Progress

## §E.1 Plan-phase Audit-Ready Signal

Plan-phase notes (authoring session 2026-10-18, iteration 1):
- Defect evidence is read from the primary checkout; reproduction status is stated per defect in `spec.md` §1 (D1 partial, D2 yes, D3 mechanism only, D4 no, D5 partial).
- Not verified by the author: real `handle-stop-goal.sh` end-to-end, `navigator-regen.sh` end-to-end, Stop block enforcement on Claude Code 2.1.302, `moai update` behavior, full Stop-hook path of the D5 patch, contents of upstream issue #1827 beyond a WebFetch summary.

Iteration 2 (2026-10-18), addressing the plan-audit report `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18.md`:
- X-1: all clarification markers removed from plan.md. Answered by user decisions: tracking scope (exactly the four files), status-line path ownership (REQ-HOOKS-003). Moved to measurement tasks with ACs: `moai update` treatment (AC-HOOKS-007), schema enforcement on 2.1.302 (AC-HOOKS-008). Decided: wrapper contract is dispatch once then exit 0 (REQ-HOOKS-001); evaluator exit-code question dropped.
- X-2: single tracking scope in REQ-HOOKS-007; the "plus any file added" clauses are deleted from AC-HOOKS-006.
- X-3: the user-specific path in `.moai/status_line.sh:29-31` is owned here (REQ-HOOKS-003, AC-HOOKS-002).
- X-4: AC-HOOKS-007 always performs the real scratch update and decides from `cmp`, with an isolated `HOME`.
- X-5: Conventions mark ACs `[coordinator-run]` and state the coordinator runs all section-3 commands.
- X-7: `related_specs` removed from the frontmatter. X-8: the update-record REQ became a measurement AC. X-9: second-hand provenance reworded as relayed by the coordinator.
- H-1: REQ-HOOKS-005/AC-HOOKS-004 pin the top-level form; AC-HOOKS-008 is the 2.1.302 live check. H-2: REQ-HOOKS-001 states exit 0. H-3: REQ-HOOKS-006 and AC-HOOKS-005 select existing directories; the application-lint bullet is removed. H-4: `export SCRATCH` in Conventions. H-5: plan task 1 edits only `:377-383` and `:387`; D4 cites `:15` and `:35`. H-6: the byte-identical clause is dropped. H-7: RED baseline in plan §C step 2. H-8: Out-of-Scope bullet for `navigator-audit.sh`. H-9: plan risk R2. H-10: gate commands run under `env -u`. H-11: heading corrected in spec-compact.md. Minor: D3 "Derived by reading"; backup copied into evidence (C3).
- Deferred with reason: gate-log visibility of skipped checks (needs no decision to start; follow-up SPEC).

Iteration 3 (2026-10-18), addressing `.moai/reports/plan-audit/SPEC-TOOLING-audit-2026-10-18-iter2.md`:
- H2-1 (minor, false failure): fixed. AC-HOOKS-004 writes the advisory re-run as `env -u MOAI_SYNC_GATE_BLOCKING -u MOAI_AUTONOMY_TIER MOAI_SYNC_GATE_BLOCKING=0 CLAUDE_PROJECT_DIR=... bash ...` (assignment after the `-u` options); the convention is stated in Conventions.
- H2-2 and C-1: fixed. `protected_sha256:` (every other hook and the `moai` binary) is recorded at the first run edit and checked with `sha256sum -c` in AC-HOOKS-006, so REQ-HOOKS-008 has a check that can fail.
- H2-3 (minor): fixed. Plan task 5 also removes the stale comment at `status_line.sh:26-28`. H2-4: accepted as stated (AC-HOOKS-007/-008 are measurements). C-2: fixed (contiguous `base_sha`, one run phase at a time, order HOOKS, ENV, GITOWN, REVGATE). C-3: fixed (scratch copy built with `tar` excluding `.git`/`.venv`; created/changed file list recorded).
- `plan_status` stays audit-ready: no blocker or major finding was open for this SPEC.

plan_status: audit-ready
plan_complete_at: 2026-10-18

## §E.2 Run-phase Evidence

Run date 2026-10-18, coordinator-run (no sub-agent; user chose direct implementation at Kickoff). `$SCRATCH` = a fresh `mktemp -d` outside any git repository under the job tmp dir; fixture scripts (`lib.sh`, `gatelib.sh`, `ac1.sh`..`ac5.sh`, `mkprobe.sh`) live there and implement the commands of `spec.md` §3 verbatim (stub contents, env, PATH, asserts). `$REPO` was the primary checkout (`/home/rico/Desktop/Project/orbit-wizard-blue`) for the RED baseline and this worktree for GREEN.

base_sha: d6337ec454185c626367d5da2d2c09f70537d1ed
run_commit: fd78095 (`Harden MoAI hook and tooling scripts and track them (SPEC-HOOKS-001)`)

### Pre-flight

protected_sha256: (absolute paths; every `.claude/hooks/moai/*.sh` of the primary checkout other than `handle-stop-goal.sh` and `sync-phase-quality-gate.sh`, plus the `moai` binary; Claude Code 2.1.302, moai-adk 3.1.2)

```
ec36521adc99f986ed9ed8c942174e8eaf7dea18f44f0a1bf6decb4ec551dda4  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/chain-event.sh
7cb76b755f4abe446c1c02d9dd0b9cd8f0143ae4a42256038b8469141778367e  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-agent-hook.sh
b6c5cda3370c7843d049e4a358305b6606c5ee4d6a149c105139b97f012ba52b  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-codex-review-gate.sh
712aea9c19363f35604666019612d2589cb6b3cbc18932267ce36cfcecf39104  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-compact.sh
59d0c8b2e18ef3b480c77c901566598cf0b7d3f4ae960ae9362c808eccb5c221  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-config-change.sh
dd66578bd7d50a68e43ff75c9aa3f170c51319ef874c806f775c4a7509656535  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-cwd-changed.sh
be7a8e708c395583350902e59b2593ae85e157e238eb613abca2d7ae5da52ab5  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-elicitation-result.sh
9a2c48b16eb02edbba0c234815d9662e624cbf3ae01297794b200cd3c911a109  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-elicitation.sh
2cffb9137e2e07a590e94830544ef9b0b11f57d8c7ea93998b310cdb31696ad4  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-file-changed.sh
10d2dc18c50b72c7e1fedb100bd778671e5fdf030b19eed42981425a467a25bf  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-harness-observe.sh
00223bd34847c25132cee6b92dddce818556cf4515992136177d6d0fd7044f7e  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-harness-observe-stop.sh
df434f623748fed329dc9ee377f510fd06c9a0b75015adf0f242e606769eb79a  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-harness-observe-subagent-stop.sh
9a94f2e1c636279ef34282bc0cf58f1ad0a7f081ab01cd5d46fcdb4ca00a3567  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-harness-observe-user-prompt-submit.sh
469583652641496ae2ea4a97e051da4e42d1c2f2dd75ef77b2a6b32e84ac9288  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-instructions-loaded.sh
2c2601fbc6777427894fa3f4855509f1ce9812f4bfcf706bab723694fdc7b0bc  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-multi-review-gate.sh
100044509278c27a6405e5a9051febcfccd8a0e6c8d3074a60bda368b56ad37e  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-notification.sh
ffac03fa3b76cdf56f4e4d52f6eed98c9d9de26a7c80c9cb150e69fbf228457c  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-permission-denied.sh
9e593fbb02dd9de1177bbd102fa3093cd9d66f010ec87fd07bf981122c4ede13  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-permission-request.sh
9026c25d19d087d1de9f0a4d32f3b8b80cfe6eb229580bf8e0a354ac9084a1a3  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-post-compact.sh
8b0d438e6c8054df91a4418f2fc7abda22e7249ecd85af81f1ff870b08c43b68  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-post-tool-failure.sh
ab8866e7161d0747949d214b12bccb804ed96d4ddb64a8727aaa8c693d4d43eb  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-post-tool.sh
b67e9c729b0554a300e86ddb84f10a8d1ee053c6c729822011170c00fd5aedfd  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-pre-tool.sh
7290390059f4e8e1f1018afce8d4099d6aabf6f945561beb860bc6024d4238d9  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-security-commit.sh
26197bd4f5431363730453735ff850302c7c9d0e1d0bfdcdb75d6f6801524bef  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-security-scan.sh
9d6983097096bbea1b20a1a188926034a055f8267d2d87649a22abb2384fd12e  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-security-turn.sh
e36b67cedce2bec92dc8e91e2328c415ce0379b03b7f7b49fcef7370daf6fe2e  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-session-end.sh
bebbfbc36751bda7e8ed68b05110dfa677d3147f112001fad4ca30c3aa09f321  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-session-start-compact.sh
946c61cfa5ed30c16222ea61979b4f92c5fa2f935db108b30789425e96816902  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-session-start-navigator.sh
5fa116a9a6213785140ffc57ee55b01f810740a3f4b077d82b8f1d80626b8aad  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-session-start.sh
0afdaa154ceaaffdc6a90dfffe6eccb02952633e044458d56032134b4aac89e4  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-stop-failure.sh
211a4ac36c977c2c549a1732ad0a03f52a33298a2f9d5e7b356de5816ab0aab0  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-stop.sh
a4622b7a9cb70b51634b154a30526084e9cf05c1b1e91cc64584ccb628fa6975  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-subagent-start.sh
5a07594f8421f371990eed65a765b50ba2df15e58ec486e3b8a2ec4e8de58833  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-subagent-stop.sh
daf1f99fb7e30bb6308ed7e95415d8bff92f556a1f9eb807c00fc975c5eb41cf  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-task-completed.sh
b5ea18db0a4d5b158310f004c23d13aa37bd39cad11b51ff6de657f4edf499e5  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-task-created.sh
984f995f6c033964f6691a6eeff74bf4f67b13b534af5890946d0c01b2f99a84  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-teammate-idle.sh
f4cfb68925c298a646d8becac5eb1c1ddb7fc5bb2360ff8ea2724333d54ca0d0  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-user-prompt-submit.sh
ca0913d6f8b2fc13edee3c23ed48d0fdb52d864d22e074ce821f711877438386  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-worktree-create.sh
81422d7cd09fc9c2ad47935ffa15cf9a078ee36417059128fde2f86e93598d91  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/handle-worktree-remove.sh
9eecf2209dd9e6c8adf3c5ee0b868c5d8269493ddf2dc3a5ccb38f543411123c  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/status-transition-ownership.sh
c901780d9246f92852368e45c9f324021e448ccacef8a355a05330575e4f055c  /home/rico/Desktop/Project/orbit-wizard-blue/.claude/hooks/moai/team-ac-verify.sh
10544506538fa7ba9966ee34eae3a1171f45a6591664b5bc9095191a097f3f15  /home/rico/.local/bin/moai
```

D5 backup diff (plan §C step 3): `diff /home/rico/.claude/jobs/fadbe668/tmp/sync-phase-quality-gate.sh.bak <primary>/.claude/hooks/moai/sync-phase-quality-gate.sh` differs only in the python branch:

```
230c230,240
<         run_step ruff c1 ruff check .
---
>         # Prefer the project virtual environment's ruff (AGENTS.md lint command);
>         # the global PATH may not carry it. Fall back to PATH ruff otherwise.
>         VENV_RUFF=""
>         for cand in "$PROJECT_ROOT/.venv/bin/ruff" "$PROJECT_ROOT/.venv/Scripts/ruff.exe"; do
>             if [ -x "$cand" ]; then VENV_RUFF="$cand"; break; fi
>         done
>         if [ -n "$VENV_RUFF" ]; then
>             run_step "$VENV_RUFF" c1 "$VENV_RUFF" check src tests tools
>         else
>             run_step ruff c1 ruff check .
>         fi
```

Original python branch (from the backup): `run_step ruff c1 ruff check .`

### Fixture note (deviation)

F2 (gate fixture) additionally commits a root-level `a.py`. Reason: when AC-HOOKS-005 deletes `src/`, the HEAD commit would otherwise have no `.py` file left and the gate exits early on its code-delta check, so the `check .` / PATH-fallback cases would not reach ruff (observed in the first RED attempt: `argv=[]`). The fixture change does not alter any expected value.

### RED baseline (unmodified files, `$REPO` = primary checkout)

All five fixtures fail as expected. AC-HOOKS-001:

```
## 1a: all three tiers resolvable, PATH tier (expect exit=0 out_lines=1 calls_lines=1)
exit=0 out_lines=3 calls_lines=3 calls=[$SCRATCH/bin/moai $SCRATCH/home/go/bin/moai $SCRATCH/home/.local/bin/moai ]
## 1b: PATH without moai -> go/bin tier (expect exit=0 calls_lines=1, ends go/bin/moai)
exit=0 out_lines=2 calls_lines=2 calls=[$SCRATCH/home/go/bin/moai $SCRATCH/home/.local/bin/moai ]
## 1c: go/bin stub deleted -> .local/bin tier (expect exit=0 calls_lines=1, ends .local/bin/moai)
exit=0 out_lines=1 calls_lines=1 calls=[$SCRATCH/home/.local/bin/moai ]
## 1d: sess2 (no goal state) (expect exit=0 out_lines=0 calls_lines=0)
exit=0 out_lines=0 calls_lines=0 calls=[]
## 1e: all stubs deleted (expect exit=0 out_lines=0)
exit=0 out_lines=0 calls_lines=0 calls=[]
```

AC-HOOKS-002:

```
## 2a: executable exec lines (expect nothing, then exit=1)
23:	exec moai statusline < "$temp_file"
30:	exec "/home/rico/.local/bin/moai" statusline < "$temp_file"
35:	exec "$HOME/go/bin/moai" statusline < "$temp_file"
40:	exec "$HOME/.local/bin/moai" statusline < "$temp_file"
exit=0
## 2b: user home path (expect nothing, then exit=1)
29:if [ -f "/home/rico/.local/bin/moai" ]; then
30:	exec "/home/rico/.local/bin/moai" statusline < "$temp_file"
exit=0
## 2c: PATH tier (expect JSON line, exit=7, files_left=0)
{"decision":"block"}
exit=7 files_left=1 calls=[$SCRATCH/bin/moai ]
## 2d: go/bin tier (expect exit=7 files_left=0)
🗿 v3.1.2
🔋 5H: ░░░░░░░░░░ 0% | 🔋 7D: ░░░░░░░░░░ 0%
📁 spec-tooling | 💾 +0 M0 ?3
exit=0 files_left=1 calls=[]
## 2e: .local/bin tier (expect exit=7 files_left=0)
🗿 v3.1.2
🔋 5H: ░░░░░░░░░░ 0% | 🔋 7D: ░░░░░░░░░░ 0%
📁 spec-tooling | 💾 +0 M0 ?3
exit=0 files_left=1 calls=[]
```

AC-HOOKS-003:

```
exit=0
## progress-map.md:
# Progress Map

| spec-id | status | phase | last-commit-sha | last-commit-at | frontier-milestone |
|---------|--------|-------|-----------------|----------------|--------------------|
| SPEC-NAVTEST-001 | draft | (untracked) |  |  | draft |
| SPEC-NAVTEST-002 | draft | v9.9.9 target | (untracked) |  | draft |
| SPEC-NAVTEST-003 | draft | v9.9.9 target | (untracked) | (untracked) | draft |
## expect 1 each:
0
0
1
## capability-map regression guard (expect 1):
1
```

AC-HOOKS-004:

```
## 4a: blocking run (expect exit=0, 1 line, then True)
exit=0
lines=1
{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"ruff failed"},"systemMessage":"sync-phase quality gate BLOCKED: ruff failed (ruff=1 (none)=0 deps_modified=1). Detail: .moai/logs/sync-quality-gate.log"}
False
## 4b: nested form still in script? (expect nothing, exit=1)
393:        printf '{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"%s"},"systemMessage":"sync-phase quality gate BLOCKED: %s (%s=%s %s=%s deps_modified=%s). Detail: .moai/logs/sync-quality-gate.log"}\n' \
exit=0
## 4c: advisory run (expect systemMessage, no decision anywhere)
exit=0
{"systemMessage":"sync-phase quality gate WARNING (advisory, not blocking): ruff failed (ruff=1 (none)=0 deps_modified=1). Heavy lint/tests run in CI. Detail: .moai/logs/sync-quality-gate.log"}
True
## 4d: stub exits 0 (expect empty gate.out)
exit=0
bytes=0
```

AC-HOOKS-005:

```
## 5a: src tests tools present (expect: check src tests tools)
exit=0
argv=[check src tests tools] gate.out_bytes=0
## 5b: tools removed (expect: check src tests)
exit=0
argv=[check src tests tools] gate.out_bytes=0
## 5c: only none left (expect: check .)
exit=0
argv=[check src tests tools] gate.out_bytes=0
## 5d: PATH fallback, src+tests (expect: check src tests)
exit=0
argv=[check .] gate.out_bytes=0
## 5e: no ruff anywhere (expect exit=0, empty gate.out)
exit=0
argv=[] gate.out_bytes=0
```

RED reading: AC-001 ran the evaluator 3 times for one Stop event (D1); AC-002 left a temp file on every branch and the script contains the home path (D2); AC-003 shifted columns for NAVTEST-001/002 (D3); AC-004 printed `False` because the block was nested (D4); AC-005 passed `tools`/`tests` that did not exist (D5, E902 risk).

### AC-HOOKS-008 measurement (before editing the gate; Claude Code 2.1.302)

`cd $SCRATCH/probe && claude -p "reply with the word ok" --setting-sources project` (probe hook registers one Stop hook; `--setting-sources project` keeps user-level hooks out of the probe). Top-level form `{"decision":"block","reason":"HOOKS001 probe"}`: `grep -c . stop.log` = 2, second payload contains `"stop_hook_active":true` -> PASS (block honored, turn continued).
Control, nested form `{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"HOOKS001 probe"}}`: `grep -c . stop.log` = 1, only `"stop_hook_active":false` -> ignored. This confirms D4 on 2.1.302.

### GREEN (hardened files, `$REPO` = this worktree)

AC-HOOKS-001 (PASS):

```
## 1a: all three tiers resolvable, PATH tier (expect exit=0 out_lines=1 calls_lines=1)
exit=0 out_lines=1 calls_lines=1 calls=[$SCRATCH/bin/moai ]
## 1b: PATH without moai -> go/bin tier (expect exit=0 calls_lines=1, ends go/bin/moai)
exit=0 out_lines=1 calls_lines=1 calls=[$SCRATCH/home/go/bin/moai ]
## 1c: go/bin stub deleted -> .local/bin tier (expect exit=0 calls_lines=1, ends .local/bin/moai)
exit=0 out_lines=1 calls_lines=1 calls=[$SCRATCH/home/.local/bin/moai ]
## 1d: sess2 (no goal state) (expect exit=0 out_lines=0 calls_lines=0)
exit=0 out_lines=0 calls_lines=0 calls=[]
## 1e: all stubs deleted (expect exit=0 out_lines=0)
exit=0 out_lines=0 calls_lines=0 calls=[]
```

AC-HOOKS-002 (PASS):

```
## 2a: executable exec lines (expect nothing, then exit=1)
exit=1
## 2b: user home path (expect nothing, then exit=1)
exit=1
## 2c: PATH tier (expect JSON line, exit=7, files_left=0)
{"decision":"block"}
exit=7 files_left=0 calls=[$SCRATCH/bin/moai ]
## 2d: go/bin tier (expect exit=7 files_left=0)
{"decision":"block"}
exit=7 files_left=0 calls=[$SCRATCH/home/go/bin/moai ]
## 2e: .local/bin tier (expect exit=7 files_left=0)
{"decision":"block"}
exit=7 files_left=0 calls=[$SCRATCH/home/.local/bin/moai ]
```

AC-HOOKS-003 (PASS):

```
exit=0
## progress-map.md:
# Progress Map

| spec-id | status | phase | last-commit-sha | last-commit-at | frontier-milestone |
|---------|--------|-------|-----------------|----------------|--------------------|
| SPEC-NAVTEST-001 | draft |  | (untracked) | (untracked) | draft |
| SPEC-NAVTEST-002 | draft | v9.9.9 target | (untracked) | (untracked) | draft |
| SPEC-NAVTEST-003 | draft | v9.9.9 target | (untracked) | (untracked) | draft |
## expect 1 each:
1
1
1
## capability-map regression guard (expect 1):
1
```

AC-HOOKS-004 (PASS):

```
## 4a: blocking run (expect exit=0, 1 line, then True)
exit=0
lines=1
{"decision":"block","reason":"ruff failed","systemMessage":"sync-phase quality gate BLOCKED: ruff failed (ruff=1 (none)=0 deps_modified=1). Detail: .moai/logs/sync-quality-gate.log"}
True
## 4b: nested form still in script? (expect nothing, exit=1)
exit=1
## 4c: advisory run (expect systemMessage, no decision anywhere)
exit=0
{"systemMessage":"sync-phase quality gate WARNING (advisory, not blocking): ruff failed (ruff=1 (none)=0 deps_modified=1). Heavy lint/tests run in CI. Detail: .moai/logs/sync-quality-gate.log"}
True
## 4d: stub exits 0 (expect empty gate.out)
exit=0
bytes=0
```

AC-HOOKS-005 (PASS):

```
## 5a: src tests tools present (expect: check src tests tools)
exit=0
argv=[check src tests tools] gate.out_bytes=0
## 5b: tools removed (expect: check src tests)
exit=0
argv=[check src tests] gate.out_bytes=0
## 5c: only none left (expect: check .)
exit=0
argv=[check .] gate.out_bytes=0
## 5d: PATH fallback, src+tests (expect: check src tests)
exit=0
argv=[check src tests] gate.out_bytes=0
## 5e: no ruff anywhere (expect exit=0, empty gate.out)
exit=0
argv=[] gate.out_bytes=0
```

`bash -n` on all four files: SYNTAX_OK. File modes unchanged (`-rwxr-xr-x`).

### AC-HOOKS-006 (PASS)

```
$ git ls-files --error-unmatch <the four paths>
.claude/hooks/moai/handle-stop-goal.sh
.claude/hooks/moai/sync-phase-quality-gate.sh
.claude/skills/moai-workflow-project/scripts/navigator-regen.sh
.moai/status_line.sh
exit=0
$ git status --porcelain -- <the four paths>
(empty)
$ git diff --name-only d6337ec..HEAD -- . ':(exclude).moai/specs'
.claude/hooks/moai/handle-stop-goal.sh
.claude/hooks/moai/sync-phase-quality-gate.sh
.claude/skills/moai-workflow-project/scripts/navigator-regen.sh
.moai/status_line.sh
$ git diff --name-only d6337ec..HEAD -- src tests tools packaging .github AGENTS.md
(empty)
$ sha256sum -c protected.sha256   # 42 entries
42 x OK, 0 failed
```

### AC-HOOKS-007 (GAP — not measured as specified)

`moai update --help` (saved): flags `--templates-only`, `--no-hooks`, `--dry-run`, `--force`, `--yes`, `--binary`, `--restore`.
The real scratch run `HOME=$SCRATCH/updhome moai update --templates-only --no-hooks --yes` was refused by the harness ("sets HOME, injecting git configuration whose effect on where git writes can't be verified"), which is risk R4. It was not re-run through a wrapper script, and not run with the real `HOME` either, because the user-level state `moai update` writes could not be bounded.
Partial evidence only: in a scratch copy of the primary checkout (`.git`, `.venv`, `.claude/worktrees` excluded) with the four hardened files overlaid, `moai update --templates-only --no-hooks --dry-run --yes` (real HOME; dry-run modifies nothing) printed:

```
Dry-run: managed cleanup preview ---
·  [dry-run] managed cleanup  385 files removed under managed paths (385 re-deployed from templates, 0 not restored)
·  [dry-run] .moai/config removed entirely  contents backed up and restored via 3-way merge by the Backup/Restore steps
[residue-cleanup] Would remove 3 deprecated paths
```

The preview does not list per-file results, so it neither shows nor rules out that the four files are among the 385 redeployed from embedded templates. Risk R1 stays open: recovery is reinstating the tracked version (`git checkout HEAD -- <four paths>`), and a per-file `cmp` result needs the run to be repeated with an isolated `HOME`.

### Process notes

- The PreToolUse quality gate runs `pytest` on `git commit` and aborted (`Fatal Python error: Aborted` in the pytest-qt `qapp` fixture) because the hook process has no `QT_QPA_PLATFORM=offscreen`. With the documented environment the suite passes: `QT_QPA_PLATFORM=offscreen ORBIT_WIZARD_DISABLE_3D=1 .venv/bin/python -m pytest -q` -> 169 passed. The commit was retried with those two variables on the command and succeeded. This is an environment issue (SPEC-ENV-001 territory), not caused by this change.
- The fixtures set `HOME`/`PATH` inside the fixture scripts (as `spec.md` §3 prescribes) for the wrappers under test; none of them touch the worktree repository.
- Primary checkout still holds the old untracked copies of the four files. Merging this branch into a checkout that has them untracked will make git refuse to overwrite them until they are removed or replaced.

## §E.3 Run-phase Audit-Ready Signal

run_status: audit-ready (AC-HOOKS-001..006 and AC-HOOKS-008 PASS with fresh runs; AC-HOOKS-007 is a Gap — see §E.2)
run_complete_at: 2026-10-18

## §E.4 Sync-phase Audit-Ready Signal

Sync date 2026-10-18, coordinator-run, Tier S, Route A (single sync commit on the current branch `worktree-spec-tooling`; no PR, no `manager-git` spawn).

Fresh checks on the sync tree (HEAD `8a6336c`):
- `bash -n` on the four hardened files: SYNTAX_OK; `git ls-files` lists all four as tracked; `grep -c "/home/rico"` on each: 0.
- `ruff check src tests tools`: All checks passed.
- `QT_QPA_PLATFORM=offscreen ORBIT_WIZARD_DISABLE_3D=1 python -m pytest -q`: 169 passed, 4 warnings (Python sources untouched by this SPEC; run to confirm no regression).

Documentation scope: `README.md` and the repository docs make no mention of the hook scripts, and no `CHANGELOG` exists, so no product docs changed. Only SPEC bookkeeping changed: `spec.md` frontmatter `status: in-progress` -> `implemented` (`updated` unchanged, same day) and this section.

Carried-over gap (not closed by sync): AC-HOOKS-007 (does `moai update` overwrite the four tracked files) was not measured as specified, see §E.2. Risk R1 stays open; recovery is `git checkout HEAD -- <four paths>`. Status stays `implemented`, not `completed`, until the branch is merged and that gap is accepted or measured.

sync_status: audit-ready
sync_complete_at: 2026-10-18
