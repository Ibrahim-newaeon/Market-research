import pytest

from market_research_crew.schemas import CompanyResearchInput


def test_accepts_minimum_inputs() -> None:
    payload = CompanyResearchInput(
        company_name="Acme",
        industry="SaaS",
    )
    assert payload.company_name == "Acme"
    assert payload.industry == "SaaS"
    assert payload.website_url is None


def test_normalizes_website_url() -> None:
    payload = CompanyResearchInput(
        company_name="Acme",
        website_url="acme.com",
        industry="SaaS",
    )
    assert payload.website_url == "https://acme.com"


def test_rejects_blank_company_name() -> None:
    with pytest.raises(Exception):
        CompanyResearchInput(
            company_name="",
            industry="SaaS",
        )
