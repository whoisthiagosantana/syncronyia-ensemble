# Functional POC: local 2048 delivery

This is a single-user, single-template experiment. It compiles declarative product,
design and task nodes from the pinned MetaGPT source using Python AST, without
importing its roles, providers, decorators or tool registry. Three native Claude
calls elaborate those instructions; native Codex produces a JSON file bundle.
This is a MetaGPT-derived planner, not an execution of the stock MetaGPT company.

## Install and prepare

Use Linux with working unprivileged `bwrap`, user systemd/cgroups, Node, Python 3.12,
Task-Spec and the official native Claude/Codex CLIs. Create a dedicated virtualenv:

```sh
uv venv --python /usr/bin/python3 .local/poc/venv
uv pip install --python .local/poc/venv/bin/python -r experiments/poc/requirements.txt
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/poc/browsers" .local/poc/venv/bin/python -m playwright install chromium
```

Use a task-owned ephemeral PostgreSQL instance and a separate test database. Do not
point tests at the run ledger: integration tests intentionally truncate their test
tables. No SQLite fallback exists. Durable environment deployment belongs in the
infrastructure repository under its own contract; no durable deployment is installed here.

Create an owner-only configuration file outside version control (mode `0600`).
The runtime directory must also be owner-only (`0700`). Configuration fields:

| Field | Meaning |
| --- | --- |
| `dsn` | Private connection to the disposable run database; never log or commit it. |
| `runtime_root` | Absolute controller-owned artifact directory. |
| `repository` | Absolute path to this trusted checkout. |
| `capacity_probe` | Trusted argv returning fresh global capacity JSON; never supplied through MCP. |
| `claude` / `codex` | Native adapter records described below. |
| `browser_site_packages` | Absolute path to the virtualenv's Python 3.12 site-packages. |
| `browser_cache` | Absolute path to the downloaded Playwright browser directory. |
| `contracts` | Map of existing canonical Task-Spec IDs to registered contracts. |

Each adapter record has absolute `binary` and `auth_file` paths, `model`, and the
exact allowlisted `effective_model`, and exact `cli_version` output. Claude also has `quota_command`, a trusted argv
returning `{readings: [{scope, percent, observed_at, resets_at}]}`. Required Claude
windows are `five_hour` and `seven_day`. Codex obtains quota through its native
App Server and requires `required_quota_windows` in configuration. Set this only
from the actual account's reported windows, not an assumption about every plan.
The pilot account reports only `seven_day`; absence of a required window blocks.
Both providers require readings below 35%, at most 300 seconds old, with future resets.

A capacity probe returns `observed_at`, `live_workers`, and `worker_limit`. The local
house integration is `python -m ensemble_poc.admission <infra_hub path>`; it reads
canonical window settings and Orca's all-run worker counts. Failure to observe
global capacity blocks the native invocation. Memory and free disk are also checked.

Pin the three acceptance harness file hashes in `acceptance_sha256`; any change
blocks verification. The upstream planning source hashes are pinned in code.

Register only a Tier 1 signed Task-Spec with exactly these four authorized paths:
`examples/ensemble-2048/{index.html,style.css,game.mjs,ui.mjs}`. Its registration is
`{spec: <relative spec path>, revision_digest: <TaskHandoff task_revision_digest>}`.
MCP cannot register contracts, change providers or authorize arbitrary projects.

Initialize the disposable ledger explicitly, then start MCP from the trusted repository:

```sh
.local/poc/venv/bin/python -m ensemble_poc --config .local/poc/config.json init
.local/poc/venv/bin/python -m ensemble_poc --config .local/poc/config.json mcp
```

Register that second command as a local stdio MCP server in the conversational
client. Its working directory must be this checkout. Do not expose it over HTTP.
Every local process running under the same OS user remains trusted; this is not a
multi-user access-control boundary.

## Demonstrate

1. Ask the client: “Create the 2048 game via Ensemble.” Call `ensemble_plan` with
   the registered `work_item_id`, intent and a unique `request_key`.
2. Poll `ensemble_status` until `planned`, or inspect the explicit blocking reason.
3. Call `ensemble_start` with that plan ID, the same work ID and a new request key.
4. Poll until `submitted`. Retrieve manifests using `ensemble_artifacts`.
5. The external coordinator independently checks the exact generated candidate,
   integrates the four files into the declared scope and uses canonical Task-Spec
   acceptance. A model review or a `submitted` state is not acceptance.
6. View the verified submission locally:

```sh
.local/poc/venv/bin/python -m ensemble_poc --config .local/poc/config.json preview <attempt UUID>
```

The command prints an actual loopback URL. The preview applies a restrictive CSP.
It is development-only and does not publish the game.

## Boundaries, checks and recovery

- Native CLIs run in a minimized filesystem with only their own subscription auth
  file mounted read-only. They are trusted binaries and share host networking for
  provider transport. Provider-only egress is **not** certified. Model tools, plugins,
  foreign MCPs and inherited user configuration are disabled; unexpected capabilities
  or provider/model resolution fail closed. Subscription execution still uses quota.
- Generated code never receives subscription files, database credentials, Task-Spec
  keys or a host checkout. Only validated regular files are materialized. Fixed
  Node and browser tests execute offline in a different namespace.
- The Node evaluator loads generated game logic into a separate runner process and VM realm without
  imports; assertions and report writing stay in the parent verifier. The outer OS boundary, not Node VM, supplies security containment.
- Native calls bind to the worker unit. Timeout and cancellation use systemd's
  control-group termination independently of the MCP connection.
- Duplicate requests return the existing attempt. Ambiguous launches remain
  `unknown` and hold the single active slot. No timer, automatic retry or crash
  recovery silently launches another model call.
- `cancel <attempt UUID>` confirms worker termination. `reconcile <attempt UUID>`
  closes an `unknown` attempt only after its unit is inactive; it never relaunches.
- One correction round is allowed, with fresh admission. Every new model call is
  checked, including planning and review. Unknown or exceeded quota stops the run.

Activate the virtualenv and set `ENSEMBLE_TEST_DSN` privately to the disposable test
database before running `python -m unittest discover -s poc_tests -v`. The suite
must fail if PostgreSQL is missing. Keep raw provider outputs and account details
out of public evidence.

Paperclip and Quadrant integration, arbitrary project generation, tool-capable
workers, organization management, production deployment and productivity claims
remain outside this POC.
