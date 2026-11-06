# Functional POC: measured native 2048 delivery

Status: bounded local pilot completed. Date: 2026-11-06.

An official MCP SDK client submitted the registered 2048 work item. Three native
Claude calls elaborated pinned MetaGPT-derived requirements, design and task nodes.
Native Codex returned four files as JSON. The controller materialized them, ran
independent offline logic and browser checks, and obtained an independent Claude
review. The result reached `submitted`; the external coordinator owns canonical
Task-Spec acceptance and Git integration. A model never accepted its own work.

## Successful path

| Observation | Measured result |
| --- | --- |
| Planning | Three sequential calls; `claude-sonnet-5-5`; native Claude Code 2.1.318 |
| Generation | One call, first candidate on the corrected runtime; `gpt-6-sol`, medium effort; native Codex CLI 0.165.0 |
| Independent game review | `claude-sonnet-5-5`, PASS |
| Logic | 149 cases passed, including directional merges, single-merge rules, score, spawn, status and conservation |
| Browser | Keyboard, direction buttons, restart and 360px viewport passed; zero external requests |
| Planning wall time | 66.52 seconds |
| Generation, tests and review wall time | 93.53 seconds |
| Controller suite | 35 discriminating tests, including real PostgreSQL and Linux boundary checks |
| Existing Phase 0 | All 29 tests remained green |

The 160.05-second successful native path excludes cold implementation, prior failed
runs, independent controller reviews, integration and final acceptance. It is not a
productivity comparison. Provider token totals were not retained by these initial
adapters; they remain unknown. API list-price estimates are not subscription charges.

Model routing: the game is one M leaf on the house's provisional standard-tier
mapping (`gpt-6-sol`, medium). Planning and adversarial review use the Sonnet
coordinator tier. No tool-capable implementation worker or extra integration front
was launched; all model calls produced data only. Peak model-call concurrency was one.

## Failure that changed the implementation

The first native pipeline generated valid game logic twice: both candidates passed
149 logic cases. Chromium failed before opening a page, and the original loop spent
its one correction round on that infrastructure failure. That attempt remained
`blocked / CORRECTION_LIMIT`; it was not relabeled successful.

Resource controls isolated the fault:

| Browser task cap | Memory cap | Observation |
| --- | --- | --- |
| 64 | 768 MB | Browser failed before page creation |
| 64 | 1 GB | Browser still failed |
| 256 | 768 MB | Same candidate passed the full browser checks |

The browser now receives a bounded 256-task cgroup. Other calls keep the 64-task
default. A pinned-harness browser positive control runs before any generation call,
so this failure cannot silently consume another code correction round. Per-revision
verification reports are retained. A fresh, explicitly requested MCP attempt then
completed the full path; no ambiguous attempt was automatically retried.

The first controller review returned CORRECT. Fixes separated candidate execution
from the assertion/reporting process, capped output during reads, fixed launch and
replay races, pinned upstream/harness bytes and verified effective native settings.
Native Sonnet revalidation returned PASS. A second focused review of the browser
resource/preflight correction also returned PASS; its hash-binding suggestion was
implemented and covered by a negative control.

## Boundary and recovery evidence

- Atomic four-file materialization succeeds. Traversal, absolute paths, duplicate
  paths, symlinks, malformed JSON and surrogate encoding are rejected before writes.
- An isolated loopback connection succeeds while a known host endpoint is denied.
  Removing network isolation makes that negative control fail.
- A synthetic key is absent. Deliberately mounting it makes the control fail.
- Timeouts and out-of-band parent cancellation terminate descendants, including a
  double-forked child. Output flooding is stopped while reading.
- Eight concurrent PostgreSQL requests create one durable attempt. New connections
  recover it; changed payloads conflict. Unknown dispatch blocks another attempt.
- Official MCP SDK 1.26.0 initialization and all five tools worked. A real negative
  facade → systemd worker → PostgreSQL roundtrip blocked missing quota with zero
  admitted native calls. The filtered SDK environment exposed a user-bus dependency,
  which is now reconstructed and independently tested.
- A generated module that prints a forged success and exits cannot forge the real
  verifier report. The direct-import mutant reproduces the original vulnerability.
- Missing auth, unexpected models, stale quota, changed harness bytes and unexpected
  tool events fail closed. Native subscription modes and effective model IDs are
  recorded privately without credential values.

## Authority, integrity and provenance

The phase-zero gate validates a coordinator-built fixed contract envelope. It does
not certify the semantic quality of model-produced planning. Planning has a separate
closed schema and remains advisory. A deterministic wire alias bridges Phase 0's
synthetic identifier vocabulary; the canonical Task-Spec ID remains authoritative.

HMAC verifies the contract, not writer identity, semantic quality or isolation.
Component acceptance uses fresh validation handoffs and baseline-discriminating evals.
The coordinator separately audited every changed path against the original
`6a892958276ea900a36d9ae2cd83df65515ec3da` baseline; refreshed handoffs do not erase
that original scope audit. No acceptance gate is skipped or downgraded.

Native CLI credentials are mounted only into trusted, tool-free provider processes.
Those processes use host networking for provider transport; provider-only egress is
not certified. Generated code executes in a different offline namespace without
subscription files, database credentials, signing keys or a host checkout. The Node
VM is an extra separation mechanism, not the OS security boundary.

Raw provider inputs/outputs, account observations and local inventories stay private.
Public evidence includes the generated bytes, deterministic tests and canonical
acceptance receipts. Reproducing HMAC Tier 1 requires the owner's private key.

## Operational limits and rollback

This supports one local user, one active attempt and one registered 2048 template.
Paperclip and Quadrant integration, arbitrary projects, tool-capable workers,
organization management and production deployment remain outside the demonstrated
scope. Upstream MetaGPT runtime, package identifiers, dependencies, attribution and
license remain unchanged.

A private, expiring owner exception authorized this pilot beyond the default 35%
admission threshold. It does not change house policy or override stale quota,
provider exhaustion, memory/disk floors or integrating-worker limits. An expired
exception blocks new model calls.

The task-owned PostgreSQL instance is disposable and separates run/test databases.
Local Python/browser dependencies and private audit evidence are retained for
reproduction. No production resource, public preview or scheduled model run is
installed. Disable the optional MCP entry, reconcile active attempts, and revert
this PR to return to the existing coordinator/harness route.

See [operation and reproduction](../../../experiments/poc/README.md).
