# Phase 0: offline proposal contract

Status: locally verified candidate; independent acceptance pending.
Run date: 2026-11-05 America/Sao_Paulo (2026-11-06 UTC). Updated after Opus review.
Base: `8a48cffb07be584eedfcdf85e6a50526bcf53940`.
Scope: [authorized offline leaf](../../../tasks/T-20261105-phase0-proposal-gate.md).
Route recommendation and actual path: TASK_SPEC with direct supervised implementation.
No factory or autonomous company was adopted.

## Observed results

| Check | Observation | Limit |
| --- | --- | --- |
| Fixture experiment | 35/35 cases passed with expected codes and record counts. | Synthetic proposals, not MetaGPT outputs. |
| Unit and CLI suite | 27/27 tests passed. | Written and executed in the implementation session; no provider-diverse review yet. |
| Always-allow mutation | Detected by 32 fixture cases. | Broad control; not the only negative control. |
| Always-reject mutation | Detected by 29 fixture cases, including valid proposals. | Ensures rejection alone cannot pass. |
| Schema-only mutation | Detected by 19 fixture cases. | Specifically removes contextual binding, scope/graph and reference checks. |
| Replay guard removed | Detected by the two replay cases. | Protection applies only to one in-memory gate instance. |
| Task-Spec authorization | Tier 1 HMAC seal; baseline evals failed before implementation, then both evals and Exit Check passed. | A seal is not proof of independent review or correctness. |
| Offline namespace probe | The same 35 cases passed; user home absent, experiment write denied, scratch write succeeded, external connection failed. | No native model/executor, provider egress, credential mount, process/cancellation or durable recovery proof. |

Machine-readable results: [phase0-results.json](phase0-results.json).
Fixture digest: `e2d7dc0cccdc1eea3251cead063100120e939226b1525eaf4fb036135cec9711`.
The report is reproducible with `python3 experiments/phase0/run_experiment.py --check`.
Use the [experiment README](../../../experiments/phase0/README.md) for the unit/CLI commands.

## What was exercised

The positive cases include an ordinary proposal, a known unresolved decision preserved in
the proposal, and hostile instruction text treated as inert data. Negative cases cover
self-acceptance, authorization/publishing fields, foreign request/work/repository/snapshot,
unmanaged/duplicate tasks, out-of-scope/noncanonical paths, undeclared dependencies, cycles,
unknown evidence, hidden/invented known decisions, malformed JSON and ambiguous duplicate
keys. Duplicate and changed-content replays leave one proposal record.

The trusted context is supplied outside the proposal, and the gate copies it before use.
The gate has no executor, tracker API, LLM provider or persistence adapter. It never opens
the paths proposed for implementation. Its own report writer is a coordinator-invoked CLI
operation with an explicit path; proposals cannot select that destination.

## Contract and write surface

The Task-Spec CLI is version 3.9.0. The owner authorized starting the existing experiment;
the coordinator materialized and sealed a bounded Phase 0 leaf. The tool's effort/path
budget warned about 15 declared paths. This was retained as one coherent M leaf because
the schema, contextual gate, synthetic fixtures and discriminating experiment form one
contract; documentation and results account for part of that explicit surface. No L/XL
work or subordinate implementation worker was dispatched.

The HMAC key stays in Git metadata, outside version control. No signing-key value or native
authentication file was exposed or included in public evidence. A repository-key holder can sign a task; the
seal does not prove the identity of a human approver. Canonical acceptance has deliberately
not been stamped while required independent review remains unavailable.

The upstream `metagpt/`, `tests/`, configuration, dependencies, workflows and license remain
outside this leaf's write surface. Python 3.12.3 and installed packages were used; the isolated
requirements record their versions. No application database or SQLite was used: this phase
has no persistence integration, and durable state is explicitly unimplemented.

## Progression gates

The owner subsequently authorized one bounded Opus review despite the previously observed
quota ceiling. The official native CLI reported subscription authentication; its successful
review resolved `opus` to `claude-opus-5-5`. It received a frozen source payload, no tools,
no MCP servers and no checkout mount. A first transport attempt failed due to missing DNS
configuration in the isolated process; the corrected transport completed. API price estimates
in native output are not subscription charges. Private account observations are not published.

Opus reviewed `3cfd3efdac674c90eb2ca8fa261f111e45013a2a` with verdict **CORRECT** (corrections
required), not ACCEPT. The current corrections have not yet received independent revalidation.
The owner requested a separate midnight validation; no acceptance or merge is implied.

Before Phase 1, obtain admitted provider-diverse review, then verify the native executor's
minimum credential/process/filesystem/network containment and trusted cancellation. The
offline namespace probe does not satisfy those requirements. Auth, effective model, fresh
quota, provider-only egress, timeout, cancellation and session behavior still need evidence.
No 2048 implementation, MCP service, company migration or productivity comparison has run.

Keep this candidate on its experiment branch until the applicable review/acceptance gates
pass. Do not infer readiness from the local tests. Rollback is disabling/removing the optional
experiment by reverting its changes; upstream runtime and canonical company state are intact.

## Resources and measurement

Declared offline-experiment model calls: 0 (not telemetry). Subordinate implementation workers: 0; one successful independent Opus review turn.
No application containers, volumes, networks or databases were created.
The offline namespace and immediate review processes exited. Repository-local ignored handoff/probe files are retained
for coordinator inspection; the HMAC key remains in repository-private Git metadata. No runtime
service remains running. Preparation and execution were local; exact phase wall-time and
token counters were not instrumented and are not inferred from tool durations.

## Opus review and coordinator corrections

| Finding on the reviewed source | Current correction or explicit boundary |
| --- | --- |
| B-4 promised graph binding while only allowed IDs/cycles were checked. | Trusted context now binds each task's exact paths, dependencies and evidence; overlapping trusted path owners and invalid/cyclic bindings are rejected. |
| Replay equivalence was underspecified. | Object keys/whitespace are canonicalized; array order is explicitly significant, with a regression case. |
| Regex end anchors admitted trailing newlines in trusted identifiers/SHA. | Strict end-of-input lookahead and hostile-context regression tests. The coordinator reproduced the original SHA case independently. |
| Replay check/write was not atomic across threads. | A per-instance lock protects check-and-record; a delayed check test exercises conflicting concurrent submissions. |
| Test claims were broader than coverage. | Added a duplicate-task case preserving the complete ID set, exact byte boundary, escaped duplicate key, surrogate, set-uniqueness, fixed-route and deep binding/snapshot cases. No claim that every conceivable mutant is killed. |
| Counters and the offline isolation narrative were not independently instrumented/reproducible. | Counters are labeled declared invariants; the offline probe is now a shipped `--isolation-probe` command. |
| CLI startup errors can also exit 1. | Callers must validate JSON decision and exit status together; startup/missing-output failures are infrastructure failures, not model rejections. |
| `--check --output` could write despite check mode. | The flags are now mutually exclusive and covered by a test. |

The reviewer did not execute tests and did not receive every top-level documentation artifact.
The coordinator checked results/artifacts separately; the midnight payload must include all
changed public files. Some proposed future controls in the review (for example human-only
acceptance) are advice, not adopted policy: canonical acceptance stays with the authorized
external coordinator under the existing autonomy rules. Full native execution and durable
state still need their own scoped evidence.

## Follow-up validation schedule

The owner requested one additional Opus validation at 2026-11-06 00:00 America/Sao_Paulo
(03:00 UTC). A local one-shot user timer runs a bounded review controller against a frozen
commit snapshot, reproduces the allowlisted offline checks, refreshes quota and capacity
admission, and then invokes native Opus with tools/MCP disabled. It records the effective
model and leaves its report locally; it cannot merge or stamp acceptance. The schedule
control was exercised with admission unarmed and confirmed no model invocation.

The private local runbook records timer identity, exact command, cancellation command,
source manifest and outcomes. This public note contains no private scheduler inventory.
Registration is not execution; the midnight result remains pending. A failed quota/capacity
check records a skip instead of silently switching provider or invoking a paid API.
