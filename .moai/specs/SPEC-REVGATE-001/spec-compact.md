# SPEC-REVGATE-001 (compact)

Auto-generated summary of `spec.md` v0.3.0 and `plan.md`: requirements, acceptance criteria, files to modify, exclusions. `spec.md` is authoritative. Depends on SPEC-HOOKS-001, SPEC-ENV-001, SPEC-GITOWN-001 (all completed first).

`<base_sha>` = `git rev-parse HEAD` taken immediately before this SPEC's first run edit (run phases one at a time: HOOKS, ENV, GITOWN, REVGATE); `export SCRATCH`; `$NODE`/`$CODEX_COMPANION` paths recorded in `progress.md` §E.2; `protected_sha256:` recorded there at the first run edit and checked with `sha256sum -c` at the end. The coordinator runs every command in `spec.md` §3; ACs marked [coordinator-run] call git, run `moai`/codex, or open live sessions.

## Situation (the repetition was relayed by the coordinator; the author did not see it)

Two Codex stop-time gates exist: the MoAI gate (`handle-codex-review-gate.sh`, registered at `.claude/settings.json:144-149`, enabled by `workflow.yaml:63` = `True`, reviews uncommitted changes, fail-open) and the Codex plugin gate (`stopReviewGate`, `False` where read). Observed messages (coordinator-captured, `observed-gate-output.md`) carry the prefix `codex review gate:` and the shape: summary, `Full review comments:`, bullets `- [P#] <title> — <path>:<lines>` with an indented body; finding sets and titles differ between runs and line ranges drift, so identity is normalized title + path. User decisions: keep the MoAI gate and add a register; the plugin gate stays disabled and unchanged. With the dependency SPECs completed first, all ten seeded entries are `fixed-in` (never suppress); the register is for later triage.

## Requirements

- **REQ-REVGATE-001**: While the MoAI gate is enabled for a workspace, the Codex plugin gate (`stopReviewGate`) shall be disabled for it.
- **REQ-REVGATE-002**: `.moai/project/review-gate-policy.md` shall state when the MoAI gate blocks, when it is advisory, how a stop passes, and the knobs that exist with `file:line` citations (user-level files as `~/...`).
- **REQ-REVGATE-003**: Where the MoAI gate is enabled, a block whose findings (observed format) are all matched by active register entries shall be allowed and shown as advisory text; matching = normalized title and project-relative path, line ranges ignored.
- **REQ-REVGATE-004**: Register `.moai/project/review-gate-acks.tsv`: six non-empty tab-separated fields (title, path, disposition, tracker, date, evidence), no header or comment lines; only `upstream-tracked`/`accepted` active; one seeded entry per distinct title in `observed-gate-output.md`; trackers include the three dependency SPECs and issue #1827.
- **REQ-REVGATE-005**: Where the MoAI gate is enabled, no stdout, a non-zero handler exit (including a timeout-style status), or non-block output shall leave the wrapper exiting 0 with no block of its own; an unresolvable `moai` exits 0 with empty output.
- **REQ-REVGATE-006**: Exactly the wrapper, the policy document, and the register shall be tracked for this change.
- **REQ-REVGATE-007**: A block with any finding matched by no active entry (including `fixed-in`-only matches), or a missing or malformed register, leaves the handler's output byte-identical.
- **REQ-REVGATE-008**: No change to the `moai` binary, the Codex plugin, `workflow.yaml` or other `.moai/config` files, `AGENTS.md`, `src/`, `tests/`, `tools/`, `packaging/`, `.github/`, other hooks, or other tracked files.

## Acceptance Criteria

| AC | Check | Pass condition |
|---|---|---|
| AC-REVGATE-001 | per workspace root: PyYAML read of `workflow.codex.review_gate.enabled`; `"$NODE" codex-companion.mjs setup --json` field `reviewGateEnabled` | wherever the first is `True`, the second is `False` |
| AC-REVGATE-002 | `git ls-files --error-unmatch`; heading count; per-knob `sed -n` check; home-path grep | tracked; `4`; each cited line contains its key; `exit=1` |
| AC-REVGATE-003 | step 0: real wrapper run once, envelope recorded, shape checked; then stub runs: both active, shifted range, one active, empty/missing/malformed/`fixed-in`, reworded title | step 0 shape matches or the SPEC fails; no block for fully acknowledged (also with shifted range); `cmp` identical to the stub's output in every other case |
| AC-REVGATE-004 | `awk -F'\t'` six-field check; one entry per distinct observed title (10); evidence verified against `observed-gate-output.md`; four tracker `grep -c -F` | prints nothing; 10; per-entry results recorded; each count at least `1` |
| AC-REVGATE-005 | stub handlers: silent exit 0, silent exit 124, `not json`; no `moai` resolvable; stub-only PATH dir with `command -v codex` failing, real binary | `exit=0` and no block decision in each; empty output without `moai`; `exit=1` for codex; Gap if the real binary cannot run |
| AC-REVGATE-006 | live session ending a turn with a deliberate defect and an empty register | the stop is blocked with the finding; Gap if no live run |
| AC-REVGATE-007 | `git ls-files --error-unmatch`, `git status --porcelain`, name-only diffs vs `<base_sha>`; `sha256sum -c` of the protected record | three paths tracked and clean; diff lists exactly them; nothing under `src tests tools packaging .github AGENTS.md`; every protected file `OK` |
| AC-REVGATE-008 | real `moai update --templates-only --no-hooks --yes` in a defined scratch copy with isolated `HOME`; `cmp`; file-list diff | verbatim output and `preserved`/`overwritten-or-merged` per file; a differing wrapper is a Gap |

## Files to Modify

- `.claude/hooks/moai/handle-codex-review-gate.sh` — register post-filter after the handler call
- `.moai/project/review-gate-policy.md` (new), `.moai/project/review-gate-acks.tsv` (new)

## Exclusions

### Out of Scope — The reviewers themselves
- No change to the `moai` binary, its Go handler, the Codex plugin or prompt, `workflow.yaml`, or the reviewer's model and effort; what counts as a finding is not changed.

### Out of Scope — The dependency fixes
- Hook, PATH, and Git-ownership defects are fixed in SPEC-HOOKS-001, SPEC-ENV-001, SPEC-GITOWN-001; only referenced here.

### Out of Scope — The multi-model gate, other Stop hooks, and other output shapes
- No change to `handle-multi-review-gate.sh`, `handle-stop-goal.sh`, `sync-phase-quality-gate.sh`, or the security hooks; no handling of any other handler output shape, no fuzzy title matching, no expiry of register entries.

### Out of Scope — Upstream
- No edit of upstream issue #1827 and no upstream patch.
