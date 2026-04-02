from market_research_crew.schemas import (
    CompetitorCandidate,
    EvidenceItem,
    MarketResearchReport,
    VerificationIssue,
    VerifiedMarketResearchReport,
)


def test_output_schema_accepts_valid_report() -> None:
    report = MarketResearchReport(
        company_name="Acme",
        website_url="https://acme.com",
        industry="SaaS",
        company_overview="Acme provides B2B messaging software for business teams.",
        products_services=["Messaging API"],
        target_audiences=["Marketing teams"],
        markets_detected=["KSA"],
        positioning_signals=["Fast onboarding"],
        competitor_candidates=[
            CompetitorCandidate(
                name="Example Competitor",
                website_url="https://competitor.com",
                reason_in_scope="Offers similar messaging API solutions.",
                evidence_summary="Public website shows overlapping business messaging features.",
            )
        ],
        channel_opportunities=["Search intent capture"],
        evidence=[
            EvidenceItem(
                claim="Acme offers messaging APIs",
                source_name="Official website",
                source_url="https://acme.com",
                source_type="official_website",
            )
        ],
        assumptions=["Potential focus on mid-market buyers"],
        missing_data=["No CRM data", "No internal revenue history"],
        confidence="medium",
        needs_human_review=False,
    )
    assert report.confidence == "medium"
    assert report.assumptions[0].startswith("[ASSUMPTION]")


def test_verified_output_escalates_high_severity_issue() -> None:
    report = VerifiedMarketResearchReport(
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
        confidence="low",
        needs_human_review=False,
        qa_passed=True,
        verification_summary="Material verification issues remain.",
        verification_issues=[
            VerificationIssue(
                severity="high",
                field_name="competitor_candidates",
                issue="Competitor list is not sufficiently supported.",
                recommendation="Remove unsupported competitors or add evidence.",
            )
        ],
        verifier_recommendations=["Run a manual competitor validation pass."],
    )
    assert report.qa_passed is False
    assert report.needs_human_review is True
    assert report.assumptions[0].startswith("[ASSUMPTION]")
