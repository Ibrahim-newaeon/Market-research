from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Dict, List, Sequence

from market_research_crew.routing import ApprovalRoute
from market_research_crew.schemas import VerifiedMarketResearchReport

ExportFormat = str


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "market-research-report"


def render_markdown_report(report: VerifiedMarketResearchReport, approval_route: ApprovalRoute) -> str:
    status_label = "Approved" if approval_route == "approved" else "Needs Human Review"
    lines: List[str] = [
        f"# Market Research Report - {report.company_name}",
        "",
        f"**Approval status:** {status_label}",
        f"**QA passed:** {'Yes' if report.qa_passed else 'No'}",
        f"**Confidence:** {report.confidence}",
        f"**Needs human review:** {'Yes' if report.needs_human_review else 'No'}",
        "",
        "## Company Overview",
        report.company_overview,
        "",
        "## Products & Services",
    ]

    lines.extend(_render_markdown_bullets(report.products_services))
    lines.extend(["", "## Target Audiences"])
    lines.extend(_render_markdown_bullets(report.target_audiences))
    lines.extend(["", "## Markets Detected"])
    lines.extend(_render_markdown_bullets(report.markets_detected))
    lines.extend(["", "## Positioning Signals"])
    lines.extend(_render_markdown_bullets(report.positioning_signals))
    lines.extend(["", "## Channel Opportunities"])
    lines.extend(_render_markdown_bullets(report.channel_opportunities))

    lines.extend(["", "## Competitor Candidates"])
    if report.competitor_candidates:
        for competitor in report.competitor_candidates:
            lines.extend([
                f"- **{competitor.name}**",
                f"  - Website: {competitor.website_url or 'Not available'}",
                f"  - Reason in scope: {competitor.reason_in_scope}",
                f"  - Evidence summary: {competitor.evidence_summary}",
            ])
    else:
        lines.append("- None")

    lines.extend(["", "## Evidence"])
    if report.evidence:
        for item in report.evidence:
            lines.append(
                f"- **Claim:** {item.claim} | **Source:** {item.source_name} | "
                f"**URL:** {item.source_url or 'Not available'} | **Type:** {item.source_type}"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Assumptions"])
    lines.extend(_render_markdown_bullets(report.assumptions))
    lines.extend(["", "## Missing Data"])
    lines.extend(_render_markdown_bullets(report.missing_data))
    lines.extend(["", "## Verification Summary", report.verification_summary, ""])
    lines.extend(["## Verification Issues"])
    if report.verification_issues:
        for issue in report.verification_issues:
            lines.extend([
                f"- **Severity:** {issue.severity}",
                f"  - Field: {issue.field_name}",
                f"  - Issue: {issue.issue}",
                f"  - Recommendation: {issue.recommendation}",
            ])
    else:
        lines.append("- None")

    lines.extend(["", "## Verifier Recommendations"])
    lines.extend(_render_markdown_bullets(report.verifier_recommendations))
    return "\n".join(lines).strip() + "\n"


def render_html_report(report: VerifiedMarketResearchReport, approval_route: ApprovalRoute) -> str:
    status_label = "Approved" if approval_route == "approved" else "Needs Human Review"
    status_class = "approved" if approval_route == "approved" else "review"

    def esc(value: str) -> str:
        return html.escape(value, quote=True)

    competitor_cards = "".join(
        f"<div class='card'><h3>{esc(item.name)}</h3><p><strong>Website:</strong> {esc(item.website_url or 'Not available')}</p>"
        f"<p><strong>Reason in scope:</strong> {esc(item.reason_in_scope)}</p>"
        f"<p><strong>Evidence summary:</strong> {esc(item.evidence_summary)}</p></div>"
        for item in report.competitor_candidates
    ) or "<p>None</p>"

    evidence_items = "".join(
        f"<li><strong>Claim:</strong> {esc(item.claim)}<br><strong>Source:</strong> {esc(item.source_name)}"
        f"<br><strong>URL:</strong> {esc(item.source_url or 'Not available')}<br><strong>Type:</strong> {esc(item.source_type)}</li>"
        for item in report.evidence
    ) or "<li>None</li>"

    verification_items = "".join(
        f"<li><strong>{esc(item.severity.title())}</strong> — {esc(item.field_name)}: {esc(item.issue)}"
        f"<br><em>Recommendation:</em> {esc(item.recommendation)}</li>"
        for item in report.verification_issues
    ) or "<li>None</li>"

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Market Research Report - {esc(report.company_name)}</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f7f8fa; color: #1f2937; }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 48px; }}
    .hero {{ background: white; border-radius: 16px; padding: 24px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08); margin-bottom: 20px; }}
    .badge {{ display: inline-block; padding: 8px 12px; border-radius: 999px; font-weight: 700; margin-bottom: 12px; }}
    .badge.approved {{ background: #dcfce7; color: #166534; }}
    .badge.review {{ background: #fef3c7; color: #92400e; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 18px; }}
    .card {{ background: white; border-radius: 16px; padding: 18px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08); margin-bottom: 16px; }}
    h1, h2, h3 {{ margin-top: 0; }}
    ul {{ padding-left: 20px; }}
    .meta p {{ margin: 6px 0; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <div class=\"badge {status_class}\">{status_label}</div>
      <h1>Market Research Report - {esc(report.company_name)}</h1>
      <div class=\"meta\">
        <p><strong>Industry:</strong> {esc(report.industry)}</p>
        <p><strong>Website:</strong> {esc(report.website_url or 'Not available')}</p>
        <p><strong>Confidence:</strong> {esc(report.confidence)}</p>
        <p><strong>QA passed:</strong> {'Yes' if report.qa_passed else 'No'}</p>
        <p><strong>Needs human review:</strong> {'Yes' if report.needs_human_review else 'No'}</p>
      </div>
      <p>{esc(report.company_overview)}</p>
    </section>

    <div class=\"grid\">
      <section class=\"card\"><h2>Products &amp; Services</h2>{_render_html_list(report.products_services)}</section>
      <section class=\"card\"><h2>Target Audiences</h2>{_render_html_list(report.target_audiences)}</section>
      <section class=\"card\"><h2>Markets Detected</h2>{_render_html_list(report.markets_detected)}</section>
      <section class=\"card\"><h2>Positioning Signals</h2>{_render_html_list(report.positioning_signals)}</section>
      <section class=\"card\"><h2>Channel Opportunities</h2>{_render_html_list(report.channel_opportunities)}</section>
      <section class=\"card\"><h2>Missing Data</h2>{_render_html_list(report.missing_data)}</section>
    </div>

    <section class=\"card\"><h2>Competitor Candidates</h2>{competitor_cards}</section>
    <section class=\"card\"><h2>Evidence</h2><ul>{evidence_items}</ul></section>
    <section class=\"card\"><h2>Assumptions</h2>{_render_html_list(report.assumptions)}</section>
    <section class=\"card\"><h2>Verification Summary</h2><p>{esc(report.verification_summary)}</p></section>
    <section class=\"card\"><h2>Verification Issues</h2><ul>{verification_items}</ul></section>
    <section class=\"card\"><h2>Verifier Recommendations</h2>{_render_html_list(report.verifier_recommendations)}</section>
  </div>
</body>
</html>
"""


def write_report_exports(
    report: VerifiedMarketResearchReport,
    output_dir: str | Path,
    export_formats: Sequence[ExportFormat],
    approval_route: ApprovalRoute,
) -> Dict[str, str]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = f"{slugify(report.company_name)}-market-research"
    artifacts: Dict[str, str] = {}

    manifest_payload = {
        "company_name": report.company_name,
        "approval_route": approval_route,
        "qa_passed": report.qa_passed,
        "needs_human_review": report.needs_human_review,
        "confidence": report.confidence,
    }
    manifest_path = target_dir / f"{base_name}-manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    artifacts["manifest_json"] = str(manifest_path)

    normalized_formats = [fmt.lower().strip() for fmt in export_formats if fmt and fmt.strip()]
    for export_format in normalized_formats:
        if export_format == "json":
            json_path = target_dir / f"{base_name}.json"
            json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
            artifacts["report_json"] = str(json_path)
        elif export_format == "md":
            markdown_path = target_dir / f"{base_name}.md"
            markdown_path.write_text(render_markdown_report(report, approval_route), encoding="utf-8")
            artifacts["report_md"] = str(markdown_path)
        elif export_format == "html":
            html_path = target_dir / f"{base_name}.html"
            html_path.write_text(render_html_report(report, approval_route), encoding="utf-8")
            artifacts["report_html"] = str(html_path)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

    return artifacts


def _render_markdown_bullets(values: Sequence[str]) -> List[str]:
    if not values:
        return ["- None"]
    return [f"- {item}" for item in values]


def _render_html_list(values: Sequence[str]) -> str:
    if not values:
        return "<p>None</p>"
    items = "".join(f"<li>{html.escape(item, quote=True)}</li>" for item in values)
    return f"<ul>{items}</ul>"
