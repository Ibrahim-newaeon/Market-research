from __future__ import annotations

from typing import Literal

from market_research_crew.schemas import VerifiedMarketResearchReport

ApprovalRoute = Literal["approved", "review_required"]


def determine_approval_route(report: VerifiedMarketResearchReport) -> ApprovalRoute:
    """Map verifier output to a routing label for the Flow approval gate."""
    if report.qa_passed and not report.needs_human_review:
        return "approved"
    return "review_required"
