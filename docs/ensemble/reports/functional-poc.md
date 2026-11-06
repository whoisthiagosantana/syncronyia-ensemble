# Functional POC implementation record

Status: implemented locally; native pilot and independent revalidation pending. Date: 2026-11-06.

The owner approved a local MCP → MetaGPT-derived planning → native Claude/Codex →
independent 2048 verification experiment. The chosen execution boundary is structured
file generation plus fixed isolated tests. Neither model receives coding tools.

Delivery route: TASK_SPEC, implemented through native harnesses. Four sealed leaves
cover boundaries, native adapters, coordinator/MCP and game verification. Advisory
file-count warnings are retained: each leaf owns one coherent component and its
discriminating tests; none is an undecomposed product implementation leaf.

## Evidence recorded so far

- Positive atomic materialization and forbidden-path, duplicate and symlink rejection.
- Real namespace checks with authorized loopback connectivity and a forbidden host
  endpoint. Removing network isolation makes the negative control fail.
- Synthetic key exclusion; deliberately mounting the key makes its control fail.
- Real child process heartbeat stops after the enforced cgroup timeout.
- PostgreSQL concurrency: eight equal requests create one durable attempt; a new
  connection returns it, and changed content conflicts.
- Unknown dispatch remains durable, blocks a second attempt and is not retried.
- MCP framing, tool discovery, strict arguments and absence of an acceptance tool.
- A fake game fails the fixed evaluator.

These checks alone do not establish a successful native game generation. Native
results, independent review, acceptance and resource disposition will be recorded
after those operations actually complete.

The first native Sonnet review returned CORRECT with one high finding (generated
logic sharing the verifier process) and narrower robustness findings. Corrections
now separate candidate execution from assertions, cap output while reading it,
fix dispatch/replay races, pin upstream inputs and verifier bytes, validate native
configuration, and preserve admission reasons. These corrections passed 31 local
tests but have not received a second independent review.

An official Python MCP SDK 1.26.0 client successfully initialized and discovered
all five tools. The simulated provider flow reaches submitted with pending external
acceptance. Simulation is not evidence of native game generation.

A real SDK → stdio facade → systemd worker → PostgreSQL negative roundtrip also
finished `blocked / QUOTA_MISSING_WINDOW` with zero admitted native invocations.
That integration exposed the SDK's filtered environment: the controller now restores
the verified local user-systemd bus instead of relying on inherited bus variables.

The next Claude call was blocked at the configured 35% short-window admission
threshold. No exception was inferred from earlier owner-authorized calls.
The native pilot must wait for renewed capacity or a separately bounded owner exception.

## Deliberate limits

Native official CLIs are trusted and use host networking for provider transport.
This is not provider-only egress certification or support for model shell tools.
Generated code runs in a separate offline namespace without credentials. The
upstream runtime and package identifiers remain unchanged.

Task-Spec remains the contract and acceptance authority. PostgreSQL stores attempts,
reservations and observation events, not another canonical organizational backlog.
Task-Spec HMAC proves contract integrity, not model authorship or semantic quality.

The POC supports one local user, one active attempt and one registered template.
Paperclip and Quadrant are future integrations, not operational dependencies.
Infrastructure used during verification is task-owned and disposable; a durable
service deployment requires a separate infrastructure contract.

See [reproduction and operation](../../../experiments/poc/README.md).

## Current handoff and resources

Implementation is retained on `experiment/functional-poc` without a merge or
Task-Spec acceptance stamp. The native game and browser positive path have not run.
The signing key and account files stay private; no model has received the host checkout.
One task-owned ephemeral PostgreSQL container and local test dependencies are
retained for immediate correction and pilot continuation. No model worker is kept
running while quota admission is blocked. The run and test databases are separate.
Peak native review concurrency for this implementation was one. No durable
infrastructure deployment, public preview, or new scheduled model run was installed.
