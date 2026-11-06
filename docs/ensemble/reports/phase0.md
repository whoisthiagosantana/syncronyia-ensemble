# Phase 0: offline proposal contract

Status: bounded offline Phase 0 accepted at Task-Spec Tier 1; native execution not certified.
Run date: 2026-11-05 America/Sao_Paulo (2026-11-06 UTC). Updated after Opus review.
Base: `8a48cffb07be584eedfcdf85e6a50526bcf53940`.
Scope: [authorized offline leaf](../../../tasks/done/T-20261105-phase0-proposal-gate.md).
Route recommendation and actual path: TASK_SPEC with direct supervised implementation.
No factory or autonomous company was adopted.

## Observed results

| Check | Observation | Limit |
| --- | --- | --- |
| Fixture experiment | 35/35 cases passed with expected codes and record counts. | Synthetic proposals, not MetaGPT outputs. |
| Unit and CLI suite | 29/29 tests passed. | Written and executed in the implementation session; no provider-diverse review yet. |
| Always-allow mutation | Detected by 32 fixture cases. | Broad control; not the only negative control. |
| Always-reject mutation | Detected by 29 fixture cases, including valid proposals. | Ensures rejection alone cannot pass. |
| Schema-only mutation | Detected by 19 fixture cases. | Specifically removes contextual binding, scope/graph and reference checks. |
| Replay guard removed | Detected by the two replay cases. | Protection applies only to one in-memory gate instance. |
| Task-Spec authorization | Tier 1 HMAC seal; baseline evals failed before implementation, then both evals and Exit Check passed. | A seal is not proof of independent review or correctness. |
| Offline namespace probe | The same 35 cases passed; user home absent, experiment write denied, scratch write succeeded, external connection failed. Network-isolation verdict is INCONCLUSIVE without a matching reachability positive control. | No native model/executor, provider egress, credential mount, process/cancellation or durable recovery proof. |

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
budget warned about 18 declared paths. This was retained as one coherent M leaf because
the schema, contextual gate, synthetic fixtures and discriminating experiment form one
contract; documentation and results account for part of that explicit surface. No L/XL
work or subordinate implementation worker was dispatched.

The HMAC key stays in Git metadata, outside version control. No signing-key value or native
authentication file was exposed or included in public evidence. A repository-key holder can sign a task; the
seal does not prove the identity of a human approver. Canonical acceptance was stamped only after independent Opus review conditions and
coordinator verification were resolved. The canonical acceptance record is versioned; a fresh clone still needs the repository
key and retained evidence to reproduce the local Tier 1 verification.

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

The bounded offline acceptance gates passed; integration may proceed under the house
autonomy rules. Do not infer native readiness from the local tests. Rollback is disabling/removing the optional
experiment by reverting its changes; upstream runtime and canonical company state are intact.

## Resources and measurement

Declared offline-experiment model calls: 0 (not telemetry). Subordinate implementation workers: 0; two successful independent Opus review turns.
No application containers, volumes, networks or databases were created.
The offline namespace and immediate review processes exited. Repository-local ignored handoff/probe files are retained
for coordinator inspection; the HMAC key remains in repository-private Git metadata. No runtime
service remains running. Preparation and execution were local; exact phase wall-time and
token counters were not instrumented and are not inferred from tool durations.

## Opus review and coordinator corrections

| Finding on the reviewed source | Current correction or explicit boundary |
| --- | --- |
| B-4 promised graph binding while only allowed IDs/cycles were checked. | Trusted context now binds each task's exact paths, dependencies and evidence; identical trusted path tokens assigned to multiple owners and invalid/cyclic bindings are rejected. Directory ancestry and filesystem alias disjointness are not established. |
| Replay equivalence was underspecified. | Parsed JSON values, object keys, insignificant whitespace and equivalent escapes are canonicalized; array order is explicitly significant and Unicode normalization is absent, with regression cases. |
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

## Immediate Opus revalidation and bounded acceptance conditions

On the owner's request, native Opus (`claude-opus-5-5`) revalidated the complete changed-file
payload at `6b7c645211373f6b3c64ce78abaa2ff0eea0827b`. Verdict: **CORRECT**. It found no
accept/reject defect in the core gate for the stated offline threat model, and independently
derived the 35-case/four-mutant result counts. It did not execute tests or verify the HMAC.
It required four narrow conditions before offline acceptance:

1. Qualify scope disjointness as string-token disjointness, deferring directory/case aliases.
2. Make hostile-context path and identifier tests otherwise internally consistent, and
   independently exercise every lexical pattern with valid and newline-bearing values.
3. Describe replay using parsed JSON equivalence, including escaped spellings and explicit
   array-order/Unicode-normalization limits.
4. Label the network observation INCONCLUSIVE without a matching positive reachability control.

The coordinator implemented those conditions in documentation, tests and probe reporting.
`gate.py` and its schema remain byte-identical to the independently reviewed core. Additional
negative-control reproductions weaken path validation and an individual identifier pattern;
each now causes the targeted test to fail without a test infrastructure error. No second
implementation executor or further model call is required for those coordinator checks.

Recommended follow-ups remain outside this acceptance claim: deterministic lock-removal
mutation evidence, automatic comparison of `--check` with a stored report, stricter fixture
byte/duplicate-key fingerprinting and richer CLI misuse classification. They do not confer
native-executor readiness. The scheduled midnight call is retained for a distinct Phase 1
readiness/authority-boundary audit, rather than repeating this code-correction review.

## Administrative scope correction

The first formal acceptance attempt passed evaluation, HMAC, baseline discrimination and
sealed-evidence checks, but correctly rejected three undeclared bootstrap paths:
`.taskspec/config`, `tasks/.gitkeep`, and the TaskPlan manifest. The coordinator amended
and re-sealed the same task to declare those existing administrative files explicitly.
No runtime write scope or acceptance criterion was weakened. A new handoff represents the
re-authorized validation attempt; the original handoff remains preserved privately.
The full change set is additionally checked against the original pre-experiment base
`8a48cffb07be584eedfcdf85e6a50526bcf53940`, which is also the explicit negative-control
baseline. This avoids treating a later handoff base as evidence of the original scope.

## Final bounded acceptance

The external coordinator resolved the four stated offline acceptance conditions without
changing the reviewed `gate.py` or schema. The final 29-test suite and 35-case experiment
passed; weakening path validation caused six targeted test failures, and weakening an
individual identifier pattern caused one, both with zero infrastructure errors. The
network probe is explicitly INCONCLUSIVE, not accepted network-containment evidence.

Canonical `taskspec accept --stamp` then passed at Tier 1: evaluation, current handoff/
revision/scope, HMAC integrity, original-baseline gold-sanity and sealed evidence policy.
The task transitioned to `done`. The original pre-experiment diff was separately checked
against all declared paths after the administrative scope correction. No check was skipped
or downgraded. The local acceptance digest is
`sha256:c37595683549764fc25cf2a590b6d51ad5064d6f602164b3e161bc305215c597`.
The native Opus verdicts themselves remained CORRECT; this final acceptance is the external
coordinator's decision after resolving their stated conditions, not a claim that Opus issued
an unqualified ACCEPT for later documentation/test edits.

Only offline Phase 0 is accepted. Durable idempotency, planning quality, provider egress,
native implementation-executor containment/cancellation and productivity remain unproven.
The midnight audit retains those questions as its distinct advisory scope.

The CLI archived the completed Task-Spec under `tasks/done/`. The unchanged canonical
[AcceptanceRecord](../../../.taskspec/acceptance/T-20261105-phase0-proposal-gate/3dd295c9-1b22-4df6-af8e-6310a10835b5.json) contains no credentials or private workspace paths.
