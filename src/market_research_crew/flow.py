from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from crewai.flow import Flow, listen, or_, router, start

from market_research_crew.crew import MarketResearchCrew
from market_research_crew.export import write_report_exports
from market_research_crew.routing import ApprovalRoute, determine_approval_route
from market_research_crew.schemas import CompanyResearchInput, VerifiedMarketResearchReport

load_dotenv()

DEFAULT_EXPORT_FORMATS = ["json", "md", "html"]


class MarketResearchFlowState(BaseModel):
    company_name: str = ""
    website_url: Optional[str] = None
    industry: str = ""
    country_focus: List[str] = Field(default_factory=list)
    research_goal: str = "general market scan"
    normalized_inputs: Dict[str, Any] = Field(default_factory=dict)
    final_report: Optional[VerifiedMarketResearchReport] = None
    approval_route: Optional[ApprovalRoute] = None
    export_formats: List[str] = Field(default_factory=lambda: DEFAULT_EXPORT_FORMATS.copy())
    output_dir: str = "output"
    artifacts: Dict[str, str] = Field(default_factory=dict)


class MarketResearchFlow(Flow[MarketResearchFlowState]):
    """Flow-first wrapper around the market research crew with an approval gate."""

    @start()
    def capture_inputs(
        self,
        company_name: str = "",
        website_url: Optional[str] = None,
        industry: str = "",
        country_focus: Optional[List[str]] = None,
        research_goal: str = "general market scan",
        export_formats: Optional[List[str]] = None,
        output_dir: str = "output",
    ) -> Dict[str, Any]:
        payload = CompanyResearchInput(
            company_name=company_name,
            website_url=website_url,
            industry=industry,
            country_focus=country_focus or [],
            research_goal=research_goal,
        )
        normalized = payload.model_dump()
        self.state.company_name = payload.company_name
        self.state.website_url = payload.website_url
        self.state.industry = payload.industry
        self.state.country_focus = payload.country_focus
        self.state.research_goal = payload.research_goal
        self.state.normalized_inputs = normalized
        self.state.export_formats = normalize_export_formats(export_formats)
        self.state.output_dir = output_dir
        return normalized

    @listen(capture_inputs)
    def run_research_crew(self, _: Dict[str, Any]) -> Dict[str, Any]:
        result = MarketResearchCrew().crew().kickoff(inputs=self.state.normalized_inputs)
        final_report = getattr(result, "pydantic", None)
        if final_report is None:
            raise ValueError("Expected a Pydantic result from the verifier task, but none was returned.")
        if not isinstance(final_report, VerifiedMarketResearchReport):
            final_report = VerifiedMarketResearchReport.model_validate(final_report)
        self.state.final_report = final_report
        return {"final_report": final_report.model_dump()}

    @router(run_research_crew)
    def approval_gate(self) -> ApprovalRoute:
        if self.state.final_report is None:
            raise ValueError("Cannot route approval gate without a verified final report.")
        route = determine_approval_route(self.state.final_report)
        self.state.approval_route = route
        return route

    @listen("approved")
    def export_approved_report(self) -> Dict[str, Any]:
        if self.state.final_report is None or self.state.approval_route is None:
            raise ValueError("Cannot export approved report without final report and approval route.")
        artifacts = write_report_exports(
            report=self.state.final_report,
            output_dir=self.state.output_dir,
            export_formats=self.state.export_formats,
            approval_route=self.state.approval_route,
        )
        self.state.artifacts.update(artifacts)
        return build_flow_result(self.state)

    @listen("review_required")
    def export_review_package(self) -> Dict[str, Any]:
        if self.state.final_report is None or self.state.approval_route is None:
            raise ValueError("Cannot export review package without final report and approval route.")
        artifacts = write_report_exports(
            report=self.state.final_report,
            output_dir=self.state.output_dir,
            export_formats=self.state.export_formats,
            approval_route=self.state.approval_route,
        )
        self.state.artifacts.update(artifacts)
        return build_flow_result(self.state)

    @listen(or_(export_approved_report, export_review_package))
    def finalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return payload


def normalize_export_formats(export_formats: Optional[List[str]]) -> List[str]:
    normalized = [fmt.lower().strip() for fmt in (export_formats or DEFAULT_EXPORT_FORMATS) if fmt and fmt.strip()]
    if not normalized:
        return DEFAULT_EXPORT_FORMATS.copy()
    return normalized


def build_flow_result(state: MarketResearchFlowState) -> Dict[str, Any]:
    return {
        "approval_route": state.approval_route,
        "artifacts": state.artifacts,
        "final_report": state.final_report.model_dump() if state.final_report else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Market Research Analyst CrewAI flow wrapper",
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
        help="Export formats to generate after the approval gate",
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


def run_cli() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        payload = build_payload(args)
        flow = MarketResearchFlow()
        result = flow.kickoff(
            inputs={
                **payload.model_dump(),
                "export_formats": args.export_formats,
                "output_dir": args.output_dir,
            }
        )
        final_output = result if isinstance(result, dict) else build_flow_result(flow.state)
        rendered = json.dumps(final_output, indent=2, ensure_ascii=False)
        print(rendered)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
    except Exception as exc:
        error_payload = {
            "error": "market_research_flow_failed",
            "message": str(exc),
        }
        print(json.dumps(error_payload, indent=2, ensure_ascii=False))
        raise


def plot() -> None:
    flow = MarketResearchFlow()
    flow.plot("market_research_flow")


if __name__ == "__main__":
    run_cli()
