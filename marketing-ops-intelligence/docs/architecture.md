# Architecture

> 22 Claude Code agents wired into a strict 11-phase pipeline, gated by
> one human approval step, measured through 8 schema-bound dashboard tabs.

## 1. Components

```
┌────────────────────────────────────────────────────────────────────┐
│  Principal  ── WhatsApp (Meta Cloud API v21.0) ──  Claude Code      │
│                                                         │           │
│                                          .claude/agents/* (22)      │
│                                          .claude/skills/*  (5)      │
│                                          .claude/commands/* (6)     │
│                                          .claude/hooks/*  (6)       │
│                                                         │           │
│     ┌──────────────── core/ ─────────────────────────────┘          │
│     │ schemas/  (Zod contracts — 7 files + barrel)                  │
│     │ db/       (pg Pool + migrations + queries)                    │
│     │ auth/     (JWT + helmet + rate-limit)                         │
│     │ whatsapp/ (Meta Cloud client, send, webhook, templates)       │
│     │ platforms/{meta,google,snap,tiktok}/                          │
│     │ utils/    (logger, rate_limit, event_id, signature_verify)    │
│     └─────────────────────────────────────────────────────────────┐ │
│                                                                    │ │
│     Postgres 16 (campaign_memory, plan_decisions, approval_state, │ │
│                  dashboard_payloads, wa_audit)                    │ │
│                                                                    │ │
│     Next.js 14 dashboard (8 schema-bound tabs)                    │ │
└────────────────────────────────────────────────────────────────────┘
```

## 2. Phase flow (strict)

1. `memory_retrieval_agent`
2. Research (parallel): market / competitor / audience / keyword
3. Planning: strategy → multi-market allocator → budget optimizer
4. `approval_manager_agent` validates
5. **Human approval gate** (48h timer, WhatsApp template)
6. Conditional `legal_review_agent` (regulated verticals)
7. Execution (parallel): meta / google / snap / tiktok / seo / geo / aeo
8. Monitoring: `anomaly_detection_agent` + `performance_agent`
9. `reporting_agent`
10. `dashboard_aggregator_agent` (8 tabs)
11. `memory_update_agent`

Deviation = HARD FAIL with explicit error to Principal.

## 3. Data flow

```
memory_context  ┐
                ├──► strategy_planner ─► allocator ─► optimizer ─► approval
research ×4  ───┘                                                     │
                                                                      ▼
                                                     approval_state.json
                                                     + wa_audit (out, tpl_plan_ready)
                                                                      │
                                     /approve_plan  ◄─ Principal ─────┘
                                            │
                                            ▼
                                 [legal_review] ─► execution ×7
                                                         │
                                                         ▼
                                              performance + anomalies
                                                         │
                                                         ▼
                                                reporting ─► dashboard
                                                         │
                                                         ▼
                                                 memory_update
```

## 4. Security boundaries

| Boundary | Enforcement |
|---|---|
| Settings `permissions.deny` | `rm -rf`, force-push, `curl \| sh`, publish |
| Hook `pre-phase-gate.sh`     | Blocks unapproved campaign activation |
| JWT middleware               | 15m access / 7d refresh / HS256, ≥32-char secret |
| Helmet                        | Strict CSP + HSTS + frame-ancestors `'none'` |
| Rate limit                    | 60/min API + 10/hr/recipient WhatsApp |
| WA webhook                    | `X-Hub-Signature-256` timing-safe verification on raw bytes |
| Parameterized SQL             | `pg` placeholders `$1..$n` — never concatenation |
| Secrets                       | env vars only; logger redacts tokens |

## 5. Non-negotiable invariants

- Memory retrieval runs before planning, always.
- Every decision cites evidence or is tagged `"unknown"` + `missing_data`.
- No paid campaign is created ACTIVE — always PAUSED, Principal flips.
- `tracking_verified:true` required before paid channels execute.
- Bilingual AR + EN parity on every customer-facing surface.
- Regulated verticals route through `legal_review_agent`.
- 8 tabs, always — empty tabs must carry a justification.
- WhatsApp via Meta Cloud API only — Twilio is forbidden.
