# Marketing Ops Intelligence

A two-part marketing-operations platform combining a **CrewAI Python
research crew** (top-level) with a **full phase-gated Claude Code
marketing pipeline** (nested `marketing-ops-intelligence/`).

The Python crew produces verified, source-cited market-research reports
suitable for external distribution. The TypeScript pipeline turns that
research into an end-to-end, human-approved, multi-market ad and content
operation across paid and free channels — with a Next.js dashboard,
Postgres + pgvector memory, and WhatsApp Cloud API approvals.

---

## Repository layout

```
Marketing-Ops-Intelligence/
├── pyproject.toml                 # Python / CrewAI project: market-research-crew
├── uv.lock                        # uv lockfile for the Python crew
├── .env.example                   # OPENAI_API_KEY, SERPER_API_KEY
├── src/market_research_crew/      # CrewAI source: crew, flow, schemas, tools
│   ├── crew.py                    # Two-agent sequential crew (analyst + verifier)
│   ├── flow.py                    # Flow wrapper with router-based approval gate
│   ├── main.py                    # CLI entrypoint (`market-research-crew`)
│   ├── routing.py                 # Approval-route decision (approved / review_required)
│   ├── export.py                  # JSON / MD / HTML report exporters
│   ├── schemas.py                 # Pydantic I/O contracts
│   ├── config/agents.yaml         # Agent personas + LLM config
│   ├── config/tasks.yaml          # Task prompts + expected outputs
│   └── tools/                     # Custom CrewAI tools
├── tests/                         # Pytest suite for the Python crew
│
└── marketing-ops-intelligence/    # Nested: full Claude Code marketing pipeline
    ├── CLAUDE.md                  # Authoritative system prompt & rules
    ├── README.md                  # Operator quick-start
    ├── .claude/                   # 23 agents, 5 skills, 6 commands, 6 hooks
    ├── core/                      # Schemas (Zod), DB, auth, WhatsApp, platforms
    ├── config/                    # Clients, budgets, models, compliance, WA templates
    ├── dashboards/                # Next.js 14 app (8 tabs, shadcn/ui, Recharts)
    ├── memory/                    # campaign_memory.json + audit_log.jsonl
    ├── tests/                     # Playwright (E2E) + k6 (load)
    ├── docs/                      # Architecture, contracts, onboarding
    ├── Dockerfile / docker-compose.yml
    └── package.json / pnpm-lock.yaml
```

---

## Part 1 — Market Research Crew (Python / CrewAI)

A two-agent, sequential CrewAI crew that produces a **verified** market
research report. The analyst drafts, the verifier independently checks
every claim against primary sources and returns a structured JSON report.

### Agents & tasks

| # | Agent | Task | Output schema |
|---|---|---|---|
| 1 | `market_research_analyst` | `draft_market_scan_task` | `MarketResearchReport` |
| 2 | `research_verifier` | `verify_market_scan_task` | `VerifiedMarketResearchReport` |

Both agents have `SerperDevTool` (web search), `ScrapeWebsiteTool`
(page fetching), and `FileReadTool`. `allow_delegation=False` and
`memory=False` keep the run deterministic and auditable.

### Flow wrapper with approval gate (`flow.py`)

`MarketResearchFlow` wraps the crew in a `@start → @listen → @router`
graph:

1. `capture_inputs` — validates CLI args against `CompanyResearchInput`.
2. `run_research_crew` — kicks off the crew, stores the verified report.
3. `approval_gate` — routes to `approved` or `review_required` based on
   `routing.determine_approval_route`.
4. `export_approved_report` / `export_review_package` — writes JSON / MD
   / HTML artifacts via `export.write_report_exports`.
5. `finalize` — returns the final payload.

### Install & run

```bash
# 1. Create the virtualenv (Python 3.11–3.13)
uv sync              # or: pip install -e ".[dev]"

# 2. Configure secrets
cp .env.example .env
# fill: OPENAI_API_KEY, SERPER_API_KEY

# 3. Run the crew directly
market-research-crew \
  --company-name "Acme Retail" \
  --industry "ecommerce" \
  --country-focus SA AE \
  --research-goal "competitor mapping" \
  --export-formats json md html \
  --output-dir output

# 4. Or run the flow wrapper
python -m market_research_crew.flow \
  --company-name "Acme Retail" --industry "ecommerce"
```

Output: a JSON payload containing `approval_route`, `artifacts` (paths to
exported files), and the full `final_report`.

### Tests

```bash
pytest                         # runs tests/ — imports, schema, routing, export
```

---

## Part 2 — Marketing Ops Intelligence Pipeline (TypeScript / Claude Code)

Phase-gated, multi-agent pipeline that replaces an in-house marketing
team across paid (Meta, Google, Snap, TikTok) and free (SEO, GEO, AEO,
email, organic social, PR) channels. Markets are **never hardcoded** —
they are resolved per-run from `config/clients/<client_id>.json` by the
phase-0 `client_resolver_agent`.

> **Authority:** `marketing-ops-intelligence/CLAUDE.md` is the source of
> truth for rules and flow.

### Pipeline

```
client_resolver → memory_retrieval → research ×4 (parallel)
    → planning ×3 → approval_manager
    → HUMAN APPROVAL GATE (48h, WhatsApp Cloud API)
    → legal_review_gate (if regulated)
    → execution ×7 (parallel, PAUSED default)
    → monitoring ×2 → reporting → dashboard_aggregator → memory_update
```

Any out-of-order step is a **hard fail**. The approval gate emits the
canonical `>>> AWAITING APPROVAL FOR {PHASE_NAME} <<<` marker and waits
for a Principal slash command.

### Components

- **23 agents** in `.claude/agents/` — dispatch / validation go to Haiku;
  synthesis and reasoning stay on Opus (see `config/models.json`).
- **5 auto-firing skills** in `.claude/skills/` — `approval-gate`,
  `gtm-patterns`, `bilingual-ar-en`, `gulf-markets`, `whatsapp-notify`.
- **6 slash commands** in `.claude/commands/` — see table below.
- **6 hooks** in `.claude/hooks/` — `pre-phase-gate`,
  `on_research_complete`, `on_plan_generated`, `on_plan_approved`,
  `on_execution_started`, `on_execution_completed`.
- **Zod-validated contracts** in `core/schemas/` for every agent I/O.
- **Next.js 14 dashboard** with 8 schema-bound tabs: Overview, Paid Media,
  SEO, GEO, AEO, Markets, Performance, Anomalies.
- **Postgres + pgvector memory** with Voyage AI embeddings (`voyage-3`,
  1024-dim); falls back to recency when `VOYAGE_API_KEY` is unset.

### Slash commands

| Command | Purpose |
|---|---|
| `/run_full_pipeline <client_id> [--markets …] [--budget …]` | Resolves client (phase 0), runs through the approval gate. |
| `/generate_plan_only <client_id> [--markets …] [--budget …]` | Phases 0–4 only; emits plan, no WhatsApp, no timer. |
| `/approve_plan` | Principal approves; unlocks execution. |
| `/edit_plan <feedback>` | Re-runs planning with Principal feedback. |
| `/decline_plan <reason>` | Terminates run, logs, WA-notifies. |
| `/get_dashboard_data [tab]` | Returns aggregated JSON for a tab. |

### WhatsApp notifications (Meta Cloud API — **not Twilio**)

All notifications go through Meta Graph API v21.0 using pre-approved
templates. Canonical names live in `config/whatsapp_templates.json`.
Webhooks are signed with `X-Hub-Signature-256` and verified against
`WA_APP_SECRET` on every inbound request.

| Event | Template |
|---|---|
| Research phase done | `tpl_research_complete` |
| Plan ready for review | `tpl_plan_ready` |
| Plan approved / declined | `tpl_plan_approved` / `tpl_plan_declined` |
| Legal review required | `tpl_legal_review_required` |
| Execution started / complete | `tpl_execution_started` / `tpl_execution_complete` |
| Anomaly detected | `tpl_anomaly_detected` |
| 48h approval timeout | `tpl_approval_timeout` |

### Client-driven multi-market schema

Every run is scoped by `ClientProfile` (validated by
`core/schemas/client.ts`). `--markets` CLI overrides must be a subset of
`client.allowed_countries`. The orchestrator rejects any agent emission
whose `country` is not in `ResolvedClientContext.selected_markets`.

### Non-negotiable rules (from `CLAUDE.md`)

- Every decision cites evidence (URL, tool + timestamp, or memory entry).
- Unknown values → literal `"unknown"` + appended to `missing_data[]`.
- Memory retrieved from Postgres **and** `memory/campaign_memory.json`
  before planning; updated after execution and reporting.
- All customer-facing output ships in AR + EN, culturally adapted.
- Attribution locked: 7-day click / 1-day view; existing customers
  excluded.
- Paid campaigns created **PAUSED**. Principal activates manually.
- `tracking_verified` **must** be `true` before any paid execution.
- Regulated verticals (medical, financial, alcohol, real-estate, crypto)
  must pass `legal_review_agent` before execution.
- Empty memory is not a halt — it sets `first_run=true` and produces a
  reduced-confidence plan.
- 24-hour WhatsApp CS window enforced; outside it, only template
  messages are permitted.
- JWT access (15m) + refresh (7d); Helmet CSP; parameterized SQL;
  least-privilege agent tools.

### Install & run

```bash
cd marketing-ops-intelligence

pnpm install
cp .env.example .env
# fill: DATABASE_URL, JWT_SECRET, VOYAGE_API_KEY,
#       WA_ACCESS_TOKEN, WA_PHONE_NUMBER_ID, WA_BUSINESS_ACCOUNT_ID,
#       WA_APP_SECRET, META_*_PIXEL_ID, …

cp config/clients/_example.json config/clients/<your-client-id>.json
# edit: client_id, vertical, allowed_countries, default_markets,
#       country_defaults[], default_total_budget_usd

docker compose up -d
pnpm db:migrate
pnpm memory:seed

claude                                           # launch Claude Code here
/run_full_pipeline <your-client-id>
/run_full_pipeline <your-client-id> --markets SA,AE --budget 120000
```

### Tests

```bash
pnpm test:unit          # Zod schema tests
pnpm test:playwright    # E2E — POM pattern, positive + negative specs
pnpm test:k6            # Load — concurrent multi-market, memory latency, dashboard
```

---

## How the two parts relate

- The **Python crew** is a standalone research producer. It can be run
  independently to generate verified reports for stakeholders.
- The **TypeScript pipeline** consumes similar research signals but at
  much larger scope — it also plans, approves, executes, monitors, and
  reports across channels.
- They share themes (evidence-grounded, approval-gated, schema-validated)
  but are wired separately: no runtime coupling between the two.

---

## Environments & secrets

Top-level Python crew (`.env.example`):

```
OPENAI_API_KEY=
SERPER_API_KEY=
```

Nested pipeline (`marketing-ops-intelligence/.env.example`) covers
database, JWT, WhatsApp Cloud API, pixel IDs, Voyage embeddings, and per-
platform credentials. Never commit `.env` — it is already in `.gitignore`.

---

## Warnings

- Paid campaigns are created **PAUSED** — the Principal activates.
- Never bypass the legal-review gate for regulated verticals.
- WhatsApp templates must be pre-approved in Meta Business Manager or
  notifications fail silently.
- Unstructured markets misallocate budget — keep client profiles tight.
- Empty memory → reduced-confidence plan, not a halt.
