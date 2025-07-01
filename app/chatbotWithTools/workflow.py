from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from .models import ResearchState, CompanyInfo, FinancialAnalysis
from utills.firecrawl import FirecrawlService
from .promts import FinancialToolsPrompts


class Workflow:
    def __init__(self,llm):
        self.firecrawl = FirecrawlService()
        self.llm = llm
        self.prompts = FinancialToolsPrompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(state_schema=ResearchState)
        graph.add_node("extract_financial_tools", self._extract_financial_tools_step)
        graph.add_node("research_financial_services_step", self._research_financial_services_step)
        graph.add_node("analyze_investment_options_step", self._analyze_investment_options_step)

        graph.set_entry_point("extract_financial_tools")
        graph.add_edge("extract_financial_tools", "research_financial_services_step")
        graph.add_edge("research_financial_services_step", "analyze_investment_options_step")
        graph.add_edge("analyze_investment_options_step", END)
        return graph.compile()

    def _extract_financial_tools_step(self, state: ResearchState) -> Dict[str, Any]:
        print(f"📊 Searching financial articles about: {state.query}")

        # Enhanced search query for financial content
        article_query = f"{state.query} financial tools comparison best platforms analysis"
        search_results = self.firecrawl.search_companies(article_query, num_results=3)

        all_content = ""
        for result in search_results.data:
            url = result.get("url", "")
            scraped = self.firecrawl.scrape_company_pages(url)
            if scraped:
                all_content += scraped.markdown[:1500] + "\n\n"

        messages = [
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_SYSTEM),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query, all_content))
        ]

        try:
            response = self.llm.invoke(messages)
            tool_names = [
                name.strip()
                for name in response.content.strip().split("\n")
                if name.strip()
            ]
            print(f"💼 Extracted financial tools: {', '.join(tool_names[:5])}")
            return {"extracted_tools": tool_names}
        except Exception as e:
            print(f"⚠️ Error extracting tools: {e}")
            return {"extracted_tools": []}

    def _analyze_financial_service(self, service_name: str, content: str) -> FinancialAnalysis:
        structured_llm = self.llm.with_structured_output(FinancialAnalysis)

        messages = [
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(service_name, content))
        ]

        try:
            analysis = structured_llm.invoke(messages)
            return analysis
        except Exception as e:
            print(f"⚠️ Error analyzing {service_name}: {e}")
            return FinancialAnalysis(
                pricing_model="Unknown",
                is_data_provider=None,
                financial_metrics=[],
                description="Analysis failed",
                api_available=None,
                market_coverage=[],
                integration_platforms=[],
                real_time_data=None,
            )

    def _research_financial_services_step(self, state: ResearchState) -> Dict[str, Any]:
        extracted_tools = getattr(state, "extracted_tools", [])

        if not extracted_tools:
            print("⚠️ No extracted financial tools found, falling back to direct search")
            # Search for popular financial tools based on query
            search_results = self.firecrawl.search_companies(f"{state.query} financial data API platform", num_results=4)
            tool_names = [
                result.get("metadata", {}).get("title", "Unknown Financial Service")
                for result in search_results.data
            ]
        else:
            tool_names = extracted_tools[:4]

        print(f"🔍 Researching financial services: {', '.join(tool_names)}")

        companies = []
        for tool_name in tool_names:
            # Search for official website of the financial service
            tool_search_results = self.firecrawl.search_companies(f"{tool_name} official website financial data", num_results=1)

            if tool_search_results and tool_search_results.data:
                result = tool_search_results.data[0]
                url = result.get("url", "")

                company = CompanyInfo(
                    name=tool_name,
                    description=result.get("markdown", ""),
                    website=url,
                    financial_metrics=[],
                    competitors=[]
                )

                # Scrape detailed information from the company's website
                scraped = self.firecrawl.scrape_company_pages(url)
                if scraped:
                    content = scraped.markdown
                    analysis = self._analyze_financial_service(company.name, content)

                    # Map analysis results to company info
                    company.pricing_model = analysis.pricing_model
                    company.is_data_provider = analysis.is_data_provider
                    company.financial_metrics = analysis.financial_metrics
                    company.description = analysis.description
                    company.api_available = analysis.api_available
                    company.market_coverage = analysis.market_coverage
                    company.integration_platforms = analysis.integration_platforms
                    company.real_time_data = analysis.real_time_data

                companies.append(company)

        return {"companies": companies}

    def _analyze_investment_options_step(self, state: ResearchState) -> Dict[str, Any]:
        print("📈 Generating financial recommendations...")

        # Prepare company data for analysis
        company_data = ", ".join([
            company.json()  for company in state.companies
        ])

        messages = [
            SystemMessage(content=self.prompts.RECOMMENDATIONS_SYSTEM),
            HumanMessage(content=self.prompts.recommendations_user(state.query, company_data))
        ]

        try:
            response = self.llm.invoke(messages)
            return {"analysis": response}
        except Exception as e:
            print(f"⚠️ Error generating recommendations: {e}")
            return {"analysis": "Unable to generate recommendations at this time."}
    
    


    def run(self, query: str):
        initial_state = ResearchState(query=query)
        final_state = self.workflow.invoke(initial_state)
        return ResearchState(**final_state) 