from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


ConfidenceLevel = Literal["high", "medium", "low"]
EvidenceSourceType = Literal[
    "official_website",
    "public_web",
    "uploaded_file",
    "app",
]
VerificationSeverity = Literal["low", "medium", "high"]


class CompanyResearchInput(BaseModel):
    company_name: str = Field(..., min_length=2, description="Target company name")
    website_url: Optional[str] = Field(
        default=None,
        description="Official website URL when available",
    )
    industry: str = Field(..., min_length=2, description="Target industry")
    country_focus: List[str] = Field(
        default_factory=list,
        description="Countries or cities to prioritize during research",
    )
    research_goal: str = Field(
        default="general market scan",
        min_length=3,
        description="Example: competitor mapping, market entry, channel scan",
    )

    @field_validator("company_name", "industry", "research_goal", mode="before")
    @classmethod
    def strip_required_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("website_url", mode="before")
    @classmethod
    def normalize_website_url(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            return cleaned
        return f"https://{cleaned}"

    @field_validator("country_focus", mode="before")
    @classmethod
    def normalize_country_focus(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        return value


class EvidenceItem(BaseModel):
    claim: str = Field(..., min_length=3)
    source_name: str = Field(..., min_length=2)
    source_url: Optional[str] = None
    source_type: EvidenceSourceType


class CompetitorCandidate(BaseModel):
    name: str = Field(..., min_length=2)
    website_url: Optional[str] = None
    reason_in_scope: str = Field(..., min_length=5)
    evidence_summary: str = Field(..., min_length=5)


class MarketResearchReport(BaseModel):
    company_name: str
    website_url: Optional[str] = None
    industry: str

    company_overview: str = Field(..., min_length=10)
    products_services: List[str] = Field(default_factory=list)
    target_audiences: List[str] = Field(default_factory=list)
    markets_detected: List[str] = Field(default_factory=list)
    positioning_signals: List[str] = Field(default_factory=list)

    competitor_candidates: List[CompetitorCandidate] = Field(default_factory=list)
    channel_opportunities: List[str] = Field(default_factory=list)

    evidence: List[EvidenceItem] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    missing_data: List[str] = Field(default_factory=list)

    confidence: ConfidenceLevel
    needs_human_review: bool

    @field_validator("assumptions")
    @classmethod
    def assumptions_should_be_labeled(cls, values: List[str]) -> List[str]:
        normalized: List[str] = []
        for item in values:
            stripped = item.strip()
            if not stripped:
                continue
            if stripped.startswith("[ASSUMPTION]"):
                normalized.append(stripped)
            else:
                normalized.append(f"[ASSUMPTION] {stripped}")
        return normalized

    @field_validator("evidence")
    @classmethod
    def evidence_can_be_empty_but_should_exist(cls, values: List[EvidenceItem]) -> List[EvidenceItem]:
        return values


class VerificationIssue(BaseModel):
    severity: VerificationSeverity
    field_name: str = Field(..., min_length=2)
    issue: str = Field(..., min_length=5)
    recommendation: str = Field(..., min_length=5)


class VerifiedMarketResearchReport(MarketResearchReport):
    qa_passed: bool
    verification_summary: str = Field(..., min_length=10)
    verification_issues: List[VerificationIssue] = Field(default_factory=list)
    verifier_recommendations: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def align_review_flags(self) -> "VerifiedMarketResearchReport":
        has_high_severity_issue = any(issue.severity == "high" for issue in self.verification_issues)
        if has_high_severity_issue:
            self.qa_passed = False
            self.needs_human_review = True
        return self
