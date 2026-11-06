# Syncronyia Ensemble

**Experimental MetaGPT fork for governed AI software delivery.**

Status: **experimental / bounded local 2048 POC demonstrated**. The accepted
[offline Phase 0](experiments/phase0/README.md) remains unchanged. The separate
[MCP and native data-generation POC](experiments/poc/README.md) completed a real
Claude planning → Codex generation → isolated logic/browser checks → Claude review
roundtrip. The [generated game](examples/ensemble-2048/index.html) uses four static files.
See the [measured results and limits](docs/ensemble/reports/functional-poc.md).
This demonstrates the fixed local template; tool-capable agents and autonomous company
operation remain unverified.
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
| [POC assessment and development flow](docs/ensemble/reports/poc-assessment-and-delivery-fit.md) | Owner gameplay confirmation, results, limits, routing recommendations and proposed Ensemble integration. |
| [Astra advisory](docs/ensemble/reviews/2026-11-05-astra-advisory.md) | Reviewed recommendations, corrections and evidence limits. |
| [Upstream provenance](docs/ensemble/upstream.md) | Baseline, license, fork scope, validation and rollback. |

The offline fixture experiment, local POC controls and real two-provider game pilot have run. See the
[Phase 0 report](docs/ensemble/reports/phase0.md) for measured results and remaining gates.
No productivity advantage or general-purpose factory readiness claim is made. Subscription execution still consumes tokens and plan quota. Provider login stays
inside official executors; this fork does not provide a shared subscription API.

## What exists today

- A named GitHub fork with upstream history, license and runtime code preserved.
- A source-backed assessment and reviewed composition proposal.
- A bounded experiment design that can fail without migrating company state.
- An offline proposal validator with synthetic cases, targeted mutations and local results.
- A separate local MCP facade, PostgreSQL attempt ledger, native data-only adapters
  and fixed offline verification harness with a measured native game pilot.

The local POC does not install or adopt a company-wide factory. GitHub Actions is disabled
for the initial research stage. The local POC enforces its bounded data-only profile; broader factory adoption and
tool-capable executor containment remain unverified. Private pilot evidence is not included in public Git.

## Upstream

MetaGPT is developed by [FoundationAgents](https://github.com/FoundationAgents/MetaGPT).
Its original documentation is preserved byte-for-byte in [README.upstream.md](README.upstream.md).
That README describes upstream capabilities and examples, not an approved execution path
for this experiment. Python imports, package metadata and the `metagpt` command retain their
upstream names until a separately scoped migration is warranted.

[MIT license](LICENSE). The Ensemble name is provisional; availability has not been established.
