# Astra architectural advisory

Date: 2026-11-05. Status: advisory, not a runtime acceptance gate.
Reviewer selection: owner-requested `gpt-6-astra`, low reasoning effort, OpenAI native
subagent runtime. The collaboration interface accepted that selection; an independent
effective-model receipt was not exposed and is not claimed.
Leaf classification: M architectural review with an explicit owner model selection and
cross-system authority/security concerns. No API-key or gateway fallback was used.

This is the coordinator's public summary of the read-only review, not its verbatim private
working report. Private company sources and environment findings are intentionally excluded.
The coordinator directly checked the consequential upstream claims against baseline
`11cdf466d042aece04fc6cfd13b28e1a70341b1f` before incorporating them.

## Recommendation

Retain MetaGPT as an experimental planning/proposal engine behind existing delivery authority.
Do not replace the company's canonical tracker or its admission/acceptance control plane
with Team memory and role messages.

## Supporting evidence checked by the coordinator

| Source | Finding |
| --- | --- |
| [`software_company.py:43`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/software_company.py#L43) | Default role hiring includes Engineer2; conditional legacy QA/review hiring is commented out. `implement=False` does not make this entry point planning-only. |
| [`team.py:59`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/team.py#L59), [`base_env.py:197`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/environment/base_env.py#L197) | JSON recovery and concurrent role execution do not by themselves demonstrate durable duplicate-safe external dispatch. |
| [`mgx_env.py:16`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/environment/mgx/mgx_env.py#L16) | Public chat/broadcast is enabled by default; role routing must not be treated as confidentiality isolation. |
| [`role_zero.py:424`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/roles/di/role_zero.py#L424) | Internal task completion is performed inside the role loop, so it cannot stand for independent acceptance. |
| [`engineer2.py:35`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/roles/di/engineer2.py#L35) | The engineer includes executable tools; a proposal-only pilot requires capability removal. |
| [`anthropic_api.py:20`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/provider/anthropic_api.py#L20), [`cost_manager.py:44`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/utils/cost_manager.py#L44) | API-provider and price-table mechanisms are distinct from native subscription execution and quota admission. |

## Architecture advice

- Keep one external transition authority, canonical work IDs, Task-Spec contracts and Git
  artifacts. Treat planner memory and completion fields as non-authoritative projections.
- Separate assurance route, planning engine and execution backend rather than present them
  as four interchangeable factories.
- Evaluate planning with synthetic fixtures first, including ambiguity, injection and replay.
  Prove the native executor adapter separately before one admitted development task.
- Compare the same scope and independent acceptance against the existing path. Reject an
  operational dependency that requires duplicate scheduling/state, API fallback or self-acceptance.
- Replacing an orchestrator does not remove isolation, credentials, quota, capacity or retry
  requirements. An issue in another product is not automatically a MetaGPT vulnerability.

## Documentation review and corrections

The same advisory worker reviewed AGENTS.md, assessment.md and architecture.md after
drafting. It found no private company details in those files and requested four corrections:
admit planning inference before calling a model; qualify adapter feasibility; route the
diagram's proposals through coordinator validation; and pin source links to upstream SHA.
Those corrections were incorporated. This is same-provider architectural review and is
not a substitute for any required cross-provider runtime acceptance.

The reviewer subsequently inspected the experiment plan, provenance document, this advisory
summary and corrected architecture. It required minimum containment/cancellation evidence
before the first live executor invocation, rather than first testing the boundary after
implementation. The phase order was corrected. No other material factual or privacy issue
was identified in the reviewed public content; repository settings remain coordinator checks.

## Scope and resources

The reviewer inspected sources and documents without executing models through subprocesses,
running the company, changing files, accessing secrets or provisioning infrastructure.
No worker branch, worktree, container, volume, image, network or database was created.
There was one advisory worker at a time. Provider quota was not exposed by this review
runtime and is recorded as unknown, not inferred from unrelated local sessions.
The review supports design exploration only; no runtime integration is certified.
