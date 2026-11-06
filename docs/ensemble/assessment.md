# Experimental assessment

Date: 2026-11-05. Status: research hypothesis; no integration is implemented.

Upstream baseline: `FoundationAgents/MetaGPT` at
[`11cdf466d042aece04fc6cfd13b28e1a70341b1f`](https://github.com/FoundationAgents/MetaGPT/tree/11cdf466d042aece04fc6cfd13b28e1a70341b1f).
Method: static source inspection, official integration documentation, and an advisory
architecture review. No end-to-end company generation or subscription adapter was executed.
The initial fork preserves upstream runtime code and the MIT license.

## Recommendation

Explore MetaGPT as a replaceable proposal and planning engine behind a governed delivery
coordinator. Do not promote its simulated company into the authority for execution,
acceptance, credentials, deployment, or company records.

MetaGPT may contribute product/architecture drafts and role-based decomposition. That is
a narrower and testable hypothesis than replacing an organizational control plane.
An organizational control plane still needs durable work ownership, dispatch admission,
recovery, identities, audit, and independently accepted completion.

## Findings from the inspected source

All line references below refer to the pinned upstream revision, not a moving branch.

| Evidence | Direct finding | Architectural consequence |
| --- | --- | --- |
| [`software_company.py:43`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/software_company.py#L43) | The default company hires TeamLeader, ProductManager, Architect, Engineer2, and DataAnalyst. Conditional legacy review/QA hiring is commented out. | Role labels and CLI options are not evidence of independent acceptance. |
| [`software_company.py:56`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/software_company.py#L56) | `implement`, `code_review`, and `run_tests` are exposed, but the related conditional hiring block is commented out. Engineer2 is hired regardless of `implement`. | `implement=False` must not be used as a safety boundary for a planning-only experiment. This does not prove that every possible internal review path is absent. |
| [`base_llm.py:35`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/provider/base_llm.py#L35), [`llm_provider_registry.py:13`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/provider/llm_provider_registry.py#L13) | LLM calls have a provider abstraction and registry. | The abstraction provides a candidate adapter seam; compatibility and operational feasibility remain unverified. |
| [`anthropic_api.py:20`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/provider/anthropic_api.py#L20), [`openai_api.py:72`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/provider/openai_api.py#L72) | These providers create API SDK clients with configured API keys. | Existing Claude/OpenAI support is not native subscription-harness integration. |
| [`team.py:59`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/team.py#L59), [`team.py:122`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/team.py#L122) | Team has JSON serialization/recovery and round/idle/balance termination. | Recovery exists; transactional acceptance and duplicate-safe external dispatch are not demonstrated by these mechanisms. |
| [`base_env.py:197`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/environment/base_env.py#L197) | Active roles execute through `asyncio.gather`. | An unrestricted integration introduces another scheduling layer. Global capacity must remain externally admitted. |
| [`mgx_env.py:16`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/environment/mgx/mgx_env.py#L16) | Public chat is enabled by default and adds broadcast recipients. | Role routing is not a confidentiality boundary. Minimize data before it enters the team. |
| [`engineer2.py:35`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/roles/di/engineer2.py#L35) | The engineer exposes editor, terminal, browser, PR, and deployment tools. | The stock company is executable agency. Proposal-only operation needs capability removal, not a prompt telling it to refrain. |
| [`role_zero.py:424`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/roles/di/role_zero.py#L424) | A role can finish its current internal task. | Internal completion must map to submitted work, not canonical acceptance. |
| [`cost_manager.py:44`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/utils/cost_manager.py#L44), [`team.py:98`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/team.py#L98) | Unknown model pricing can leave monetary cost unchanged; balance is checked before an environment round. | This is neither a subscription quota guard nor reservation of global capacity. Concurrent/in-round usage remains a separate concern. |
| [`deployer.py:4`](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/tools/libs/deployer.py#L4) | The deployment helper is marked unimplemented and returns a fixed local URL with success wording. | Deployment text is not evidence of a deployed service. Exclude this tool from the proposed pilot. |

The inspected Python/config/dependency surfaces did not reveal an MCP server or native
Claude Code/Codex execution adapter. This is a bounded search result, not a proof about all
branches, third-party extensions, or future upstream versions.

## Native subscription executors

The proposed adapters invoke official, unmodified executors under the user's own login:

| Executor | Candidate interface | Work still required |
| --- | --- | --- |
| Claude Code | `claude -p`, JSON output, explicit session continuation | Pin the CLI; verify effective model/auth mode, allowed tools, sessions, cancellation, and quota behavior. |
| Codex | `codex exec --json`; optionally App Server for richer session/control integration | Pin the interface; verify effective model/auth mode, event parsing, resume, cancellation, and rate-limit observations. |

Official sources: [Claude programmatic execution](https://code.claude.com/docs/en/headless),
[Claude authentication/integration conditions](https://code.claude.com/docs/en/legal-and-compliance#authentication-and-credential-use),
[Codex non-interactive execution](https://developers.openai.com/codex/noninteractive/),
[Codex authentication](https://developers.openai.com/codex/auth/), and
[Codex App Server](https://developers.openai.com/codex/app-server/).

These interfaces establish integration possibilities, not successful operation of this fork.
Subscription use still consumes tokens and plan quota. It is not free or unlimited inference.
Each user signs in through the provider's own flow. Do not turn subscription credentials
into a generic API service or collect/intermediate user session tokens.

Two adapter designs are possible:

1. **Completion adapter:** translate individual BaseLLM calls to bounded native CLI calls.
   This preserves more of MetaGPT's loop but requires strict output contracts and may resend
   context. Tool permissions must match the call's intent.
2. **Task executor adapter:** give an authorized task to the native harness and collect its
   artifacts/events. This preserves the executor's coding loop but changes MetaGPT's role.

Prefer task-level execution for implementation and proposal-only role work for planning.
Do not let two independent agent loops both own the same files or dispatch decision.
Eliminating API dependence requires covering planning/coordinator calls as well as coding;
replacing only Engineer2 would leave residual API-backed paths.

## MCP feasibility

A thin MCP facade can submit a request to an external run service and expose status,
artifacts, and cancellation. It must not call the stock `generate_repo` in-process as a
trusted request handler. That function mutates shared configuration and starts its own
event loop. Model execution and MCP protocol handling should have separate lifecycles.

Candidate tools are specified in [the architecture proposal](architecture.md). They are
names for future interfaces, not installed tools. An initial service can use explicit job
IDs and polling; native MCP task support requires compatibility verification in each client.
See [MCP server documentation](https://modelcontextprotocol.io/docs/develop/build-server)
and [MCP tasks](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks).

## Company management and Paperclip

An organization/work tracker and a software generation engine serve different purposes.
Evaluate [Paperclip](https://github.com/paperclipai/paperclip) as a candidate organizational
control plane and Ensemble as a candidate planning engine. Neither is automatically the
security, acceptance, or infrastructure boundary of the composed system.

Changing the engine does not eliminate the need for per-task isolation, credential scoping,
network policy, trustworthy quota data, admission of all execution origins, artifact provenance,
duplicate-safe retries, or independent acceptance. Specific findings from a separate private
pilot must not be described as MetaGPT vulnerabilities without target-specific verification.
Private pilot inventories, incident evidence, credentials, and source records are excluded
from this public fork. No Paperclip migration is authorized or implemented here.

## Composition with existing delivery tools

| Component | Proposed responsibility | Must not be inferred |
| --- | --- | --- |
| Canonical organizational tracker | Goals, priorities, ownership, stable work IDs and operational projections | A tracker status grants execution or acceptance. |
| External delivery coordinator | Route selection, admission, reconciliation and integration authority | A model's recommendation is an authorization. |
| Quadrant | Product admission and dependent-front decomposition when selected and actually available | A discoverable skill means a factory is installed or ready. |
| Task-Spec | Sealed scope, handoff, validation and acceptance evidence | A seal proves correct requirements, isolation, or semantic correctness. |
| Native harness | Execute one admitted task within assigned capabilities | A successful process exit means the task is accepted. |
| Ensemble | Draft plans, dependencies and role-based proposals against canonical IDs | Internal team memory becomes the company record. |
| Infrastructure/admission services | Isolation, resource reservations, credentials and quota policy | Role prompts enforce these controls. |

Route selection should be compositional: the work's assurance needs, the planning engine,
and the execution backend are separate decisions. A simple 2048 game may need only a
harness and bounded acceptance; an explicit request for Ensemble should select that engine
without waiving the same controls. See [architecture](architecture.md) and
[the falsifiable experiment](experiment-plan.md).

## Limits and decision

The docs-only fork is useful for preserving a research hypothesis. It does not establish a
governed company, an installed factory, a working MCP integration, or productivity gains.
Keep the existing path as baseline. Admit Ensemble as an operational dependency only if a
bounded comparison shows fewer accepted planning defects or less corrective work without
unmanaged authority, duplicate state, or disproportionate maintenance/usage overhead.

An [Astra advisory review](reviews/2026-11-05-astra-advisory.md) supports the proposal-only
starting point. It is architectural advice, not independent runtime acceptance.
