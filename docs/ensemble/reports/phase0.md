# Phase 0: offline proposal contract

Status: locally verified candidate; independent acceptance pending.
Run date: 2026-11-05 America/Sao_Paulo (2026-11-06 UTC).
Base: `8a48cffb07be584eedfcdf85e6a50526bcf53940`.
Scope: [authorized offline leaf](../../../tasks/T-20261105-phase0-proposal-gate.md).
Route recommendation and actual path: TASK_SPEC with direct supervised implementation.
No factory or autonomous company was adopted.

## Observed results

| Check | Observation | Limit |
| --- | --- | --- |
| Fixture experiment | 28/28 cases passed with expected codes and record counts. | Synthetic proposals, not MetaGPT outputs. |
| Unit and CLI suite | 19/19 tests passed. | Written and executed in the implementation session; no provider-diverse review yet. |
| Always-allow mutation | Detected by 25 fixture cases. | Broad control; not the only negative control. |
| Always-reject mutation | Detected by 22 fixture cases, including valid proposals. | Ensures rejection alone cannot pass. |
| Schema-only mutation | Detected by 14 fixture cases. | Specifically removes contextual binding, scope/graph and reference checks. |
| Replay guard removed | Detected by the two replay cases. | Protection applies only to one in-memory gate instance. |
| Task-Spec authorization | Tier 1 HMAC seal; baseline evals failed before implementation, then both evals and Exit Check passed. | A seal is not proof of independent review or correctness. |
| Offline namespace probe | The same 28 cases passed; user home absent, experiment write denied, scratch write succeeded, external connection failed. | No native model/executor, provider egress, credential mount, process/cancellation or durable recovery proof. |

Machine-readable results: [phase0-results.json](phase0-results.json).
Fixture digest: `ace4f6c71ad99f26cfc6850aa2bea45c4a9fa1d2297b47bfc565dcbbadd39e29`.
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

No additional native model call was launched. The available independent-review provider's
local quota observation was above the applicable admission ceiling. That private account
observation is not reproduced in the public repository. Review remains pending rather than
being replaced with a same-session claim of independent acceptance.

Before Phase 1, obtain admitted provider-diverse review, then verify the native executor's
minimum credential/process/filesystem/network containment and trusted cancellation. The
offline namespace probe does not satisfy those requirements. Auth, effective model, fresh
quota, provider-only egress, timeout, cancellation and session behavior still need evidence.
No 2048 implementation, MCP service, company migration or productivity comparison has run.

Keep this candidate on its experiment branch until the applicable review/acceptance gates
pass. Do not infer readiness from the local tests. Rollback is disabling/removing the optional
experiment by reverting its changes; upstream runtime and canonical company state are intact.

## Resources and measurement

Experiment model calls: 0. Subordinate workers: 0. Containers, volumes, networks and databases created: 0.
The offline namespace process exited. Repository-local ignored handoff/probe files are retained
for coordinator inspection; the HMAC key remains in repository-private Git metadata. No runtime
service remains running. Preparation and execution were local; exact phase wall-time and
token counters were not instrumented and are not inferred from tool durations.
