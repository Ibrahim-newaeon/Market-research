from __future__ import annotations

from typing import Any, Dict

from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, after_kickoff, agent, before_kickoff, crew, task
from crewai_tools import FileReadTool, ScrapeWebsiteTool, SerperDevTool

from market_research_crew.schemas import CompanyResearchInput, MarketResearchReport, VerifiedMarketResearchReport

load_dotenv()


@CrewBase
class MarketResearchCrew:
    """Two-agent CrewAI market research crew with a verification pass."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @before_kickoff
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        payload = CompanyResearchInput.model_validate(inputs)
        return payload.model_dump()

    @after_kickoff
    def passthrough_result(self, result: Any) -> Any:
        return result

    @agent
    def market_research_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_research_analyst"],
            verbose=True,
            allow_delegation=False,
            memory=False,
            tools=[
                SerperDevTool(),
                ScrapeWebsiteTool(),
                FileReadTool(),
            ],
        )

    @agent
    def research_verifier(self) -> Agent:
        return Agent(
            config=self.agents_config["research_verifier"],
            verbose=True,
            allow_delegation=False,
            memory=False,
            tools=[
                SerperDevTool(),
                ScrapeWebsiteTool(),
                FileReadTool(),
            ],
        )

    @task
    def draft_market_scan_task(self) -> Task:
        return Task(
            config=self.tasks_config["draft_market_scan_task"],
            output_pydantic=MarketResearchReport,
        )

    @task
    def verify_market_scan_task(self) -> Task:
        return Task(
            config=self.tasks_config["verify_market_scan_task"],
            output_pydantic=VerifiedMarketResearchReport,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.market_research_analyst(), self.research_verifier()],
            tasks=[self.draft_market_scan_task(), self.verify_market_scan_task()],
            process=Process.sequential,
            verbose=True,
        )
