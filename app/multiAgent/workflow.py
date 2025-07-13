from typing import Dict, Any ,Annotated 
from langgraph.graph import StateGraph, END ,START
from langchain_core.messages import HumanMessage, SystemMessage
from utills.firecrawl import FirecrawlService
#from .promts import FinancialToolsPrompts
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from .tools import fetch_articles, fetch_arxives
from langchain_core.tools import tool
from chatbot.models import FirecrawlInput
import logging


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # You can change this to INFO or ERROR as needed
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class State(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    economic_term: str  
    symbol: str         

class Workflow:
    def __init__(self,llm):
        self.firecrawl = FirecrawlService()
        self.llm = llm
        #self.prompts = FinancialToolsPrompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(state_schema=State)
        graph.add_node("chatbot", self._chatbot)
        graph.add_node("fetch_articles" , fetch_articles) 
        graph.add_node("fetch_arxives" , fetch_arxives) 
        graph.add_node("firecrawl_search" , self._firecrawl_search) #(FIRECRAWL)
        #graph.set_entry_point("extract_financial_tools")
        graph.add_edge(START , "fetch_articles")
        graph.add_edge("fetch_articles", "fetch_arxives")
        graph.add_edge("fetch_arxives" , "firecrawl_search")
        graph.add_edge("firecrawl_search" , "chatbot")
        graph.add_edge("chatbot", END)
        return graph.compile()

    def _chatbot(self, state: State):
        return {"messages": [self.llm.invoke(state["messages"])] }

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
                for result_item in search_results['data'][:3]:  # Limit to first 3 results
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
            logging.info(f"Completed firecrawl search for query: {query}. \n answer: {consolidated_message} \n" )
            # Return updated state with new messages
            return {"messages": [result_message, consolidated_message]}
            
        except Exception as e:
            error_message = SystemMessage(
                content=f"Error during firecrawl search: {str(e)}"
            )
            return {"messages": [error_message]}

    