# Syncronyia Ensemble

**Experimental MetaGPT fork for governed AI software delivery.**

Status: **research / offline Phase 0 candidate**. A synthetic proposal gate and its local
tests exist in [experiments/phase0](experiments/phase0/README.md); independent acceptance is
pending. Native Claude Code/Codex execution, MCP tools and governed orchestration remain
**proposed, not implemented**.
The Python runtime and dependencies remain upstream MetaGPT at
[`11cdf466`](https://github.com/FoundationAgents/MetaGPT/tree/11cdf466d042aece04fc6cfd13b28e1a70341b1f).
Running the upstream company can invoke executable tools and API-backed models.

## Research hypothesis

A team of product, architecture and engineering roles may improve planning. Ensemble
explores whether those roles can produce useful proposals inside an existing governed
delivery process, using native authenticated executors and independent acceptance.

The initial recommendation is to use Ensemble as an optional **proposal/planning engine**.
One external coordinator retains execution admission and acceptance authority. The
canonical tracker keeps organizational work IDs; Task-Spec carries the contract; a native
harness executes; Quadrant supplies broader intake/decomposition when selected and ready.
Internal role messages and completion fields do not authorize work or certify delivery.

## Assessment and proposed experiment

| Document | Content |
| --- | --- |
| [Assessment](docs/ensemble/assessment.md) | Source findings, native subscription feasibility, MCP and company-management limits. |
| [Architecture proposal](docs/ensemble/architecture.md) | Single authority, state ownership, route selection, admission and proposed MCP tools. |
| [Experiment plan](docs/ensemble/experiment-plan.md) | Offline fixtures, native executor proof, 2048 pilot and rejection criteria. |
| [Astra advisory](docs/ensemble/reviews/2026-11-05-astra-advisory.md) | Reviewed recommendations, corrections and evidence limits. |
| [Upstream provenance](docs/ensemble/upstream.md) | Baseline, license, fork scope, validation and rollback. |

The offline fixture experiment has run; the model-driven pilot has not. See the
[Phase 0 report](docs/ensemble/reports/phase0.md) for measured results and remaining gates.
No productivity, native-auth or MCP readiness claim is made. Subscription execution still consumes tokens and plan quota. Provider login stays
inside official executors; this fork does not provide a shared subscription API.

## What exists today

- A named GitHub fork with upstream history, license and runtime code preserved.
- A source-backed assessment and reviewed composition proposal.
- A bounded experiment design that can fail without migrating company state.
- An offline proposal validator with synthetic cases, targeted mutations and local results.

No factory is installed or adopted by creating this repository. GitHub Actions is disabled
for the initial research stage. Runtime tool restrictions and admission remain design
requirements, not enforced features. Private pilot evidence is not included in public Git.

## Upstream

MetaGPT is developed by [FoundationAgents](https://github.com/FoundationAgents/MetaGPT).
Its original documentation is preserved byte-for-byte in [README.upstream.md](README.upstream.md).
That README describes upstream capabilities and examples, not an approved execution path
for this experiment. Python imports, package metadata and the `metagpt` command retain their
upstream names until a separately scoped migration is warranted.

[MIT license](LICENSE). The Ensemble name is provisional; availability has not been established.
