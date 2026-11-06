# Offline proposal contract experiment

Status: candidate, locally tested; corrections after provider-diverse Opus review await revalidation and canonical acceptance.
The fixture experiment launches no MetaGPT runtime, model, native executor, tracker, queue or
implementation task. A separate owner-authorized native Opus review examined an earlier candidate.

## Run

Use Python 3.12 and the isolated requirements below. The recorded run used already installed
packages; it did not install upstream MetaGPT dependencies or contact a provider.

```bash
python3 -m pip install -r experiments/phase0/requirements.txt
python3 -m unittest discover -s experiments/phase0 -p 'test_*.py' -v
python3 experiments/phase0/run_experiment.py --check
python3 experiments/phase0/gate.py \
  --context experiments/phase0/fixtures/context.json \
  --proposal experiments/phase0/fixtures/proposal.json
```

The dependency installation is optional if the pinned packages are already present. Prefer
a dedicated virtual environment for a fresh installation. The commands run only this isolated
experiment; they do not use the upstream pytest configuration or its API-backed test surfaces.

## Trusted input and untrusted proposal

The operator supplies `context.json` independently of model output. It binds an existing
synthetic request/work item, repository SHA, selected route/engine, complete allowed task
IDs, permitted paths, dependency/evidence references, exact per-task bindings and known
unresolved decision IDs.
The context is validated and copied. A digest covers its canonical JSON bytes.

The untrusted proposal must conform to the closed schema and those context constraints.
It can contain explanatory text but no command, accepted state, authorization envelope or
publishing action. Text remains inert data; passing validation does not make it trusted.
The gate checks graph cycles, exact task coverage, unresolved decisions, reference scope,
and exact per-task path/dependency/evidence sets. Trusted task scopes must be disjoint.
It does not assess whether summaries are good, evidence is true, dependencies are complete
in the business domain, or an additional decision should have been discovered.

The gate returns `RECORDED` only for a structurally/contextually valid proposal. That records
its digest in the current object, not a canonical work item, authorization or execution.
Replaying equivalent JSON in that object returns `DUPLICATE`; equivalence ignores object-key
order and whitespace only. Array order remains significant for replay and snapshot digests.
Altered valid content for the
same request returns `REQUEST_CONFLICT`. Restarting the object loses those records.
The replay check and record write are locked for concurrent submissions within one object.
Neither the CLI nor this in-memory check provides durable idempotency or exactly-once dispatch.

CLI exit codes: 0 for a recorded proposal, 1 for proposal rejection, 2 for invalid/missing
operator input, provided a valid recognized JSON decision is present. A startup/import failure,
missing JSON, traceback or unknown result is an infrastructure failure, not a model rejection.
Callers must validate both structured stdout and process status. Results contain stable codes and digests, not copies of hostile input.
Inputs are bounded to 64 KiB; duplicate JSON keys and NaN/Infinity literals are rejected; numeric overflow in another schema position is rejected
by schema validation. Paths use
a restricted, canonical relative POSIX vocabulary. String/path validation is not a filesystem
or symlink sandbox; the gate never opens proposal-referenced paths.

## Evidence

`fixtures/cases.json` drives the reproducible experiment. The local run passed 35 cases and
27 unit/CLI tests. Four broken gate variants were detected: always allow, always reject,
schema-only checks, and removal of replay detection. The schema-only and replay mutations
exercise contextual and retry invariants specifically; broad controls also test the harness.

An additional local probe ran the same 35 cases under a read-only mount in an isolated
network namespace, with no user home and with temporary writes allowed only in the scratch
filesystem. This does not verify provider networking, native login, process containment or
trusted cancellation for an actual coding executor.

See the [report](../../docs/ensemble/reports/phase0.md) and
[machine-readable fixture results](../../docs/ensemble/reports/phase0-results.json).

Reproduce the isolated fixture probe on Linux with Bubblewrap:

```bash
python3 experiments/phase0/run_experiment.py --isolation-probe
```

Model/implementation counters in the report are declared architectural invariants, not provider
telemetry. New decision IDs are rejected; an unexpected business question requires an operator
context revision rather than silently adding an approved decision. Path strings are never
passed to an executor; option-like or case-alias paths remain a separate live-execution concern.
