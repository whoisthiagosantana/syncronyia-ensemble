---
id: T-20261105-phase0-proposal-gate
title: "Validate synthetic planning proposals without execution authority"
status: done
format_version: 3
profile: standard
effort: M
budget_iterations: 15
agent: codex
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: [README.md, AGENTS.md, .gitignore, docs/ensemble/experiment-plan.md, .taskspec/config, tasks/.gitkeep, tasks/.plans/phase0-proposal-gate.yaml]
creates_paths: [experiments/phase0/gate.py, experiments/phase0/contract.schema.json, experiments/phase0/requirements.txt, experiments/phase0/test_gate.py, experiments/phase0/run_experiment.py, experiments/phase0/fixtures/context.json, experiments/phase0/fixtures/proposal.json, experiments/phase0/fixtures/cases.json, experiments/phase0/README.md, docs/ensemble/reports/phase0.md, docs/ensemble/reports/phase0-results.json]
source_note: "Owner authorized starting the existing experiment; this leaf implements offline Phase 0 only."
created: "2026-11-05T00:00:00Z"
tags: []
owner: (none)
priority: P2
severity: feature
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: (none)
source_action_item: (none)
tracker_ref: (none)
execution_backend: codex
signed_off: true
signed_off_by: thiago
signed_off_at: 2026-11-06T02:15:52Z
accepted: true
accepted_by: thiago
accepted_at: 2026-11-06T02:16:29Z
signed_off_sig: hmac-sha256-v3:a9566bca:a6c23b6e4b35edff001d7d5a8c4d8a8843c026c814c8677259bc548cf9b697e3
accepted_tier: 1
accepted_attempt_id: 3dd295c9-1b22-4df6-af8e-6310a10835b5
accepted_authorization_ref: hmac-sha256-v3:a9566bca:a6c23b6e4b35edff001d7d5a8c4d8a8843c026c814c8677259bc548cf9b697e3
acceptance_record_digest: sha256:c37595683549764fc25cf2a590b6d51ad5064d6f602164b3e161bc305215c597
---

# Validate synthetic planning proposals without execution authority

> **Why:** The experiment needs a reproducible proposal contract before native model integration.

## Goal

Validate and record synthetic proposals while rejecting authority escalation, scope defects and replay.

## Context

The task also owns its repository-local Task-Spec bootstrap config, backlog marker and
TaskPlan manifest. These three administrative paths were omitted from the initial scope;
the coordinator explicitly authorizes and re-seals them without extending runtime scope.

No model calls, upstream runtime changes, network, database, production data or execution adapters in the Phase 0 implementation. A separate read-only review may use an admitted native harness.

## Behavior

- **B-1** — GIVEN a trusted synthetic snapshot and a valid bound proposal WHEN the offline gate validates and records it THEN one proposal is recorded with no implementation or authorization action
- **B-2** — GIVEN malformed, foreign, out-of-scope or authority-bearing proposal content WHEN the gate evaluates it THEN it rejects the proposal with a stable reason and records no proposal
- **B-3** — GIVEN a proposal for a request already recorded in this gate instance WHEN it is replayed or replaced THEN equivalent replay is duplicate and altered content conflicts without creating another record
- **B-4** — GIVEN missing trusted decisions or invalid dependencies and evidence references WHEN a proposal hides a decision or changes the declared graph or references THEN the external gate rejects it and reports a deterministic reason

## Success Criteria

```bash
# eval_1: Positive controls, hostile inputs and contextual binding checks pass.
eval_1() {
  python3 -m unittest discover -s experiments/phase0 -p 'test_*.py' -v
}

# eval_2: Reproducible fixture experiment and always-allow/always-reject controls discriminate.
eval_2() {
  python3 experiments/phase0/run_experiment.py --check
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Positive controls, hostile inputs and contextual binding checks pass."
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3, B-4]
    terminal: true
    expected_duration_sec: 10
  - id: eval_2
    description: "Reproducible fixture experiment and always-allow/always-reject controls discriminate."
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3, B-4]
    terminal: true
    expected_duration_sec: 10
retry_policy:
  max_iterations: 15
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [code, tests]
  required_tools: [git, bash]
  timeout_minutes: 30
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1 && eval_2
```

## Rollback Plan

Revert only the declared write surface and park the task with context.

## Observability Hooks

(none — no runtime observability required)

## Anti-Patterns

- Do not interpret valid proposal as signed authorization or accepted delivery.
- Do not claim in-memory deduplication is durable or exactly-once dispatch.
- Do not invoke MetaGPT tools, executors or paid APIs from the offline gate.

## Do-Not-Touch

- `metagpt/`
- `tests/`
- `config/`
- `requirements.txt`
- `setup.py`
- `.github/`
- `LICENSE`

## Open Questions

(none — this task is fully specified)
