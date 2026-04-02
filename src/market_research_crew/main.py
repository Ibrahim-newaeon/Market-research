from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from market_research_crew.crew import MarketResearchCrew
from market_research_crew.export import write_report_exports
from market_research_crew.routing import determine_approval_route
from market_research_crew.schemas import CompanyResearchInput, VerifiedMarketResearchReport

load_dotenv()

DEFAULT_EXPORT_FORMATS = ["json", "md", "html"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Market Research Analyst CrewAI crew",
    )
    parser.add_argument("--company-name", required=True, help="Target company name")
    parser.add_argument("--website-url", default=None, help="Official company website")
    parser.add_argument("--industry", required=True, help="Target industry")
    parser.add_argument(
        "--country-focus",
        nargs="*",
        default=[],
        help="Countries or cities to prioritize",
    )
    parser.add_argument(
        "--research-goal",
        default="general market scan",
        help="Example: competitor mapping, channel scan, market entry",
    )
    parser.add_argument(
        "--export-formats",
        nargs="+",
        default=DEFAULT_EXPORT_FORMATS.copy(),
        choices=["json", "md", "html"],
        help="Export formats to generate from the verified report",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to write exported artifacts to",
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Optional file path to save the final JSON output",
    )
    return parser


def build_payload(args: argparse.Namespace) -> CompanyResearchInput:
    return CompanyResearchInput(
        company_name=args.company_name,
        website_url=args.website_url,
        industry=args.industry,
        country_focus=args.country_focus,
        research_goal=args.research_goal,
    )


def serialize_result(result: Any) -> Dict[str, Any]:
    pydantic_result = getattr(result, "pydantic", None)
    if pydantic_result is not None:
        return pydantic_result.model_dump()

    json_result = getattr(result, "json_dict", None)
    if json_result is not None:
        return json_result

    raw_result = getattr(result, "raw", None)
    if raw_result is not None:
        return {"raw": raw_result}

    return {"raw": str(result)}


def run_cli() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        payload = build_payload(args)
        result = MarketResearchCrew().crew().kickoff(inputs=payload.model_dump())
        final_output = serialize_result(result)

        validated_report = VerifiedMarketResearchReport.model_validate(final_output)
        approval_route = determine_approval_route(validated_report)
        artifacts = write_report_exports(
            report=validated_report,
            output_dir=args.output_dir,
            export_formats=args.export_formats,
            approval_route=approval_route,
        )

        response_payload = {
            "approval_route": approval_route,
            "artifacts": artifacts,
            "final_report": validated_report.model_dump(),
        }
        rendered = json.dumps(response_payload, indent=2, ensure_ascii=False)
        print(rendered)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
    except Exception as exc:
        error_payload = {
            "error": "market_research_run_failed",
            "message": str(exc),
        }
        print(json.dumps(error_payload, indent=2, ensure_ascii=False))
        raise


if __name__ == "__main__":
    run_cli()
