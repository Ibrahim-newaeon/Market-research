import json
from pathlib import Path

from market_research_crew.export import render_html_report, render_markdown_report, write_report_exports
from market_research_crew.schemas import EvidenceItem, VerificationIssue, VerifiedMarketResearchReport


def build_report() -> VerifiedMarketResearchReport:
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
        needs_human_review=True,
        qa_passed=False,
        verification_summary="Verification found unsupported competitor evidence.",
        verification_issues=[
            VerificationIssue(
                severity="medium",
                field_name="competitor_candidates",
                issue="Competitor evidence is incomplete.",
                recommendation="Add stronger evidence or remove the competitor.",
            )
        ],
        verifier_recommendations=["Perform a manual competitor validation pass."],
    )


def test_markdown_and_html_include_review_status() -> None:
    report = build_report()
    markdown = render_markdown_report(report, "review_required")
    html = render_html_report(report, "review_required")

    assert "Needs Human Review" in markdown
    assert "Needs Human Review" in html
    assert "Verification found unsupported competitor evidence." in markdown
    assert "Verification found unsupported competitor evidence." in html


def test_write_report_exports_creates_requested_files(tmp_path: Path) -> None:
    report = build_report()
    artifacts = write_report_exports(
        report=report,
        output_dir=tmp_path,
        export_formats=["json", "md", "html"],
        approval_route="review_required",
    )

    assert set(artifacts.keys()) == {"manifest_json", "report_json", "report_md", "report_html"}
    manifest = json.loads(Path(artifacts["manifest_json"]).read_text(encoding="utf-8"))
    assert manifest["approval_route"] == "review_required"
    assert Path(artifacts["report_json"]).exists()
    assert Path(artifacts["report_md"]).exists()
    assert Path(artifacts["report_html"]).exists()
