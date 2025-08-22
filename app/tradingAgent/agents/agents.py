from typing import Dict, Any ,Annotated 
from langgraph.graph import StateGraph, END ,START
from langchain_core.messages import HumanMessage, SystemMessage
from utills.firecrawl import FirecrawlService
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from tradingAgent.core.tools import get_ticker_data_poly, get_stock_data_yahoo, get_reddit_vibe, get_related_articles
from langchain_core.tools import tool
from .tradingAgents import TradingAgents
#from chatbot.models import FirecrawlInput
import logging


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # You can change this to INFO or ERROR as needed
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_preferences: dict
    query: str
    economic_term: str
    symbol: str
    strategy: str
    human_approved: bool
    market_data: dict
    sentiment_data: dict
    signals: dict
    portfolio_allocation: dict
    risk_assessment: dict
    execution_plan: dict
    trade_results: dict
    monitoring_data: dict    

class Workflow_tradingAgent:
    def __init__(self, llm, user_prefs, FirecrawlService):
        self.firecrawl = FirecrawlService()
        self.llm = llm
        self.user_prefs = user_prefs
        self.agents = TradingAgents(llm, user_prefs)
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(state_schema=State)
        # Add all agent nodes
        graph.add_node("user_agent", self.agents.user_agent)
        graph.add_node("strategy_chooser_agent", self.agents.strategy_chooser_agent)
        graph.add_node("human_approval_agent", self.agents.human_approval_agent)
        # Data Ingest Agents
        graph.add_node("polygon_api_agent", self.agents.polygon_api_agent)
        graph.add_node("reddit_agent", self.agents.reddit_agent)
        graph.add_node("news_articles_agent", self.agents.news_articles_agent)
        graph.add_node("firecrawl_agent", self._firecrawl_search)
        # Sentiment Agents
        graph.add_node("sentiment_analysis_agent", self.agents.sentiment_analysis_agent)
        # Signal/Alpha Agents
        graph.add_node("signal_alpha_agent", self.agents.signal_alpha_agent)
        # Portfolio Manager Agent
        graph.add_node("portfolio_manager_agent", self.agents.portfolio_manager_agent)
        # Risk Manager Agent
        graph.add_node("risk_manager_agent", self.agents.risk_manager_agent)
        # Execution Agent
        graph.add_node("execution_agent", self.agents.execution_agent)
        # Virtual/Live Trading Agents
        graph.add_node("virtual_backtester_agent", self.agents.virtual_backtester_agent)
        graph.add_node("live_broker_agent", self.agents.live_broker_agent)
        # Monitoring Agent
        graph.add_node("monitoring_agent", self.agents.monitoring_agent)
        # Final Response Agent
        graph.add_node("chatbot", self.agents.chatbot)
        ##################################################################################
        # Define the workflow edges according to your scheme
        graph.add_edge(START, "user_agent")
        graph.add_edge("user_agent", "strategy_chooser_agent")
        graph.add_edge("strategy_chooser_agent", "human_approval_agent")
        graph.add_edge("human_approval_agent", "polygon_api_agent")
        graph.add_edge("polygon_api_agent", "reddit_agent")
        graph.add_edge("reddit_agent", "news_articles_agent")
        graph.add_edge("news_articles_agent", "firecrawl_agent")
        # Sentiment analysis
        graph.add_edge("firecrawl_agent", "sentiment_analysis_agent")
        # Signal generation
        graph.add_edge("sentiment_analysis_agent", "signal_alpha_agent")
        # Portfolio management
        graph.add_edge("signal_alpha_agent", "portfolio_manager_agent")
        # Risk management
        graph.add_edge("portfolio_manager_agent", "risk_manager_agent")
        # Execution
        graph.add_edge("risk_manager_agent", "execution_agent")
        # Conditional routing based on mode (virtual/live)
        graph.add_conditional_edges(
            "execution_agent",
            self.agents.route_execution_mode,
            {
                "virtual": "virtual_backtester_agent",
                "live": "live_broker_agent"
            }
        )
        # Both paths lead to monitoring
        graph.add_edge("virtual_backtester_agent", "monitoring_agent")
        graph.add_edge("live_broker_agent", "monitoring_agent")
        # Final response
        graph.add_edge("monitoring_agent", "chatbot")
        graph.add_edge("chatbot", "polygon_api_agent")  

        return graph.compile()

    #def _chatbot(self, state: State):
    #    return {"messages": [self.llm.invoke(state["messages"])] }

    
    #@tool(description="FireCrawl for advance crawling websites related to the economic terms Query")
    def _firecrawl_search(self, state: State):
        query = state.get("query", "financial market")
        
        try:
            # Get serialized results
            search_results = self.firecrawl.search_financial_services(query)
            
            # Create a system message with the search results
            result_message = SystemMessage(
                content=f"Firecrawl search results for query '{query}':\n{json.dumps(search_results, indent=2)}"
            )
            
            # Initialize firecrawl_data list
            firecrawl_data = []
            
            # Process search results if they exist
            if search_results and isinstance(search_results, dict) and search_results.get('data'):
                for result_item in search_results['data'][:5]:  # Limit to first 3 results
                    if isinstance(result_item, dict) and result_item.get('url'):
                        scraped_data = self.firecrawl.scrape_financial_website(url=result_item['url'])
                        if scraped_data:
                            firecrawl_data.append(scraped_data)
            
            # Get market data
            market_data = self.firecrawl.search_market_data(query=query)
            if market_data:
                firecrawl_data.append(market_data)
            
            # Get economic data
            economic_data = self.firecrawl.scrape_economic_data(indicator=query)
            if economic_data:
                firecrawl_data.append(economic_data)
            
            # Create consolidated message with all data
            consolidated_message = SystemMessage(
                content=f"Firecrawl crawling results for query '{query}':\n{json.dumps(firecrawl_data, indent=2)}"
            )
            #logging.info(f"Completed firecrawl search for query: {query}. \n answer: {consolidated_message} \n" )
            # Return updated state with new messages
            return {"messages": [result_message, consolidated_message]}
            
        except Exception as e:
            error_message = SystemMessage(
                content=f"Error during firecrawl search: {str(e)}"
            )
            return {"messages": [error_message]}
