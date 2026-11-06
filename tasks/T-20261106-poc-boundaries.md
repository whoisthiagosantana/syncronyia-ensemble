---
id: T-20261106-poc-boundaries
title: "Constrain generated artifacts and isolate fixed verifiers"
status: ready
format_version: 3
profile: standard
effort: M
budget_iterations: 15
agent: codex
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: []
creates_paths: [ensemble_poc/__init__.py, ensemble_poc/contracts.py, ensemble_poc/containment.py, poc_tests/test_boundaries.py]
source_note: "Owner approved the functional POC plan and explicitly requested implementation."
created: "2026-11-06T00:00:00Z"
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
signed_off_at: 2026-11-06T02:45:47Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:a9566bca:c19e527c1d12363abef9497f74e1ad06b05c6b2c2c74ca36d68e90a3a4193205
---

# Constrain generated artifacts and isolate fixed verifiers

> **Why:** Demonstrate a bounded MCP to Ensemble to native subscription to independently verified 2048 path.

## Goal

Constrain generated artifacts and isolate fixed verifiers.

## Context

Local experimental POC only. Native models produce data without tools. Preserve upstream runtime. No public deployment or real tenant data. PostgreSQL for persistence.

## Behavior

- **B-1** — GIVEN a valid scoped input WHEN the component processes it THEN the bounded positive path returns verifiable artifacts and explicit state
- **B-2** — GIVEN a hostile input or unavailable required capability WHEN the component processes it THEN it fails closed without granting authority or launching duplicate execution

## Success Criteria

```bash
# eval_1: Discriminating positive and negative component tests.
eval_1() {
  python3 -m unittest poc_tests.test_boundaries -v
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Discriminating positive and negative component tests."
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
    terminal: true
    expected_duration_sec: 60
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
eval_1
```

## Rollback Plan

Revert only the declared write surface and park the task with context.

## Observability Hooks

(none — no runtime observability required)

## Anti-Patterns

- Do not claim native success from simulation.
- Do not give models signing keys, shell tools or acceptance authority.

## Do-Not-Touch

- `metagpt/`
- `tests/`
- `config/`
- `requirements.txt`
- `setup.py`
- `LICENSE`
- `.github/`

## Open Questions

(none — this task is fully specified)
