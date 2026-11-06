---
id: T-20261106-poc-native
title: "Compile upstream planning instructions and admit native data-only calls"
status: ready
format_version: 3
profile: standard
effort: M
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20261106-poc-boundaries]
supersedes: (none)
touches_paths: []
creates_paths: [ensemble_poc/planner.py, ensemble_poc/native.py, ensemble_poc/admission.py, poc_tests/test_native.py]
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
signed_off_at: 2026-11-06T02:45:51Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:a9566bca:a9c88a514ab0f63abd7040d8c4133fb2ead0603c5ef0bc1951131112edd6b4fa
---

# Compile upstream planning instructions and admit native data-only calls

> **Why:** Demonstrate a bounded MCP to Ensemble to native subscription to independently verified 2048 path.

## Goal

Compile upstream planning instructions and admit native data-only calls.

## Context

Local experimental POC only. Native models produce data without tools. Preserve upstream runtime. No public deployment or real tenant data. PostgreSQL for persistence.

## Behavior

- **B-1** — GIVEN a valid scoped input WHEN the component processes it THEN the bounded positive path returns verifiable artifacts and explicit state
- **B-2** — GIVEN a hostile input or unavailable required capability WHEN the component processes it THEN it fails closed without granting authority or launching duplicate execution

## Success Criteria

```bash
# eval_1: Discriminating positive and negative component tests.
eval_1() {
  python3 -m unittest poc_tests.test_native -v
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
