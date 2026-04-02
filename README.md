# Market Research Analyst - CrewAI Flow-First MVP

Two-agent CrewAI implementation for evidence-first market research when you only have:
- company name
- website URL (optional but preferred)
- industry

## What this version does
- scans the official website if provided
- searches the public web for market and competitor signals
- creates a draft report with a research analyst agent
- runs a verifier agent that audits and corrects the draft
- routes the verified report through an approval gate
- exports the final result as JSON, Markdown, and/or HTML
- works without CRM or historical internal knowledge

## Approval gate behavior
- `approved`: exported when `qa_passed=true` and `needs_human_review=false`
- `review_required`: exported when verification issues remain or human review is required

Both paths still export artifacts, but the manifest and rendered report clearly show the approval status.

## Project structure

```text
market-research-crew/
├── .env.example
├── knowledge/
├── pyproject.toml
├── README.md
├── src/
│   └── market_research_crew/
│       ├── __init__.py
│       ├── crew.py
│       ├── export.py
│       ├── flow.py
│       ├── main.py
│       ├── routing.py
│       ├── schemas.py
│       ├── config/
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       └── tools/
│           └── __init__.py
└── tests/
    ├── test_export.py
    ├── test_input_schema.py
    ├── test_output_schema.py
    └── test_routing.py
```

## Setup

```bash
uv sync
cp .env.example .env
```

Add your keys to `.env`:

```bash
OPENAI_API_KEY=...
SERPER_API_KEY=...
```

## Run the crew directly

```bash
uv run market-research-crew \
  --company-name "Midas Furniture" \
  --website-url "https://www.example.com" \
  --industry "Furniture Retail" \
  --country-focus KSA Kuwait \
  --research-goal "competitor mapping" \
  --export-formats json md html \
  --output-dir output
```

## Run the Flow wrapper

```bash
uv run market-research-flow \
  --company-name "Midas Furniture" \
  --website-url "https://www.example.com" \
  --industry "Furniture Retail" \
  --country-focus KSA Kuwait \
  --research-goal "competitor mapping" \
  --export-formats json md html \
  --output-dir output
```

## Exported artifacts

The export step writes a report bundle such as:

```text
output/
├── midas-furniture-market-research.json
├── midas-furniture-market-research.md
├── midas-furniture-market-research.html
└── midas-furniture-market-research-manifest.json
```

The manifest file includes:
- company_name
- approval_route
- qa_passed
- needs_human_review
- confidence

## Plot the flow

```bash
python -c "from market_research_crew.flow import plot; plot()"
```

## Test

```bash
pytest
```

## Notes
- The crew remains focused on public-signal research because there is no CRM or internal history.
- The verifier agent is intended to catch weak evidence, unsupported competitors, and mislabeled assumptions.
- The Flow is the preferred production entrypoint because it adds state, routing, and artifact export control.
