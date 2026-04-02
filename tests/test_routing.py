from market_research_crew.routing import determine_approval_route
from market_research_crew.schemas import EvidenceItem, VerifiedMarketResearchReport


def build_report(*, qa_passed: bool, needs_human_review: bool) -> VerifiedMarketResearchReport:
    return VerifiedMarketResearchReport(
        company_name="Acme",
        website_url="https://acme.com",
        industry="SaaS",
        company_overview="Acme provides B2B messaging software for business teams.",
        products_services=["Messaging API"],
        target_audiences=["Marketing teams"],
        markets_detected=["KSA"],
        positioning_signals=["Fast onboarding"],
        competitor_candidates=[],
        channel_opportunities=["Search intent capture"],
        evidence=[
            EvidenceItem(
                claim="Acme offers messaging APIs",
                source_name="Official website",
                source_url="https://acme.com",
                source_type="official_website",
            )
        ],
        assumptions=["Mid-market focus inferred from site copy"],
        missing_data=["No CRM data"],
        confidence="medium",
        needs_human_review=needs_human_review,
        qa_passed=qa_passed,
        verification_summary="Verification completed.",
        verification_issues=[],
        verifier_recommendations=["Continue with manual review only when new evidence appears."],
    )


def test_approval_route_is_approved_when_qa_passes() -> None:
    report = build_report(qa_passed=True, needs_human_review=False)
    assert determine_approval_route(report) == "approved"


def test_approval_route_is_review_required_when_human_review_is_needed() -> None:
    report = build_report(qa_passed=False, needs_human_review=True)
    assert determine_approval_route(report) == "review_required"
