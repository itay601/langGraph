from typing import Dict, Any ,Annotated 
from langgraph.graph import StateGraph, END ,START
from langchain_core.messages import HumanMessage, SystemMessage
from utills.firecrawl import FirecrawlService
#from .promts import FinancialToolsPrompts
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from .tools import fetch_articles 
from langchain_core.tools import tool
from chatbot.models import FirecrawlInput

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
        graph.add_node("fetch_articles" , fetch_articles) #tool database articles data
        #graph.add_node("fetch_company_stock_data" , fetch_company_stock_data) #tool (if specific company in data)
        graph.add_node("firecrawl_search" , self._firecrawl_search) #tool CRAWLING WEBSITES (FIRECRAWL)
        #graph.set_entry_point("extract_financial_tools")
        graph.add_edge(START , "fetch_articles")
        graph.add_edge("fetch_articles" , "firecrawl_search")
        graph.add_edge("firecrawl_search" , "chatbot")
        graph.add_edge("chatbot", END)
        return graph.compile()

    def _chatbot(self, state: State):
        return {"messages": [self.llm.invoke(state["messages"])] }

    #@tool(description="FireCrawl for advance crawling websites related to the economic terms Query")
    def _firecrawl_search(self, state: State):
        query = state.get("query", "financial market")
        
        results = self.firecrawl.search_financial_services(query)
        result_message1 = SystemMessage(
            content=f"Firecrawl search results for query '{query}':\n"
        )
        
        firecrawl_data = []
        for res, index in results:
            firecrawl_data.append(self.firecrawl.scrape_financial_website(url=res))
            result_message2 = SystemMessage(
               content=f"Firecrawl scrape_financial_website for url:'{res}':\n"
            )

        firecrawl_data.append(self.firecrawl.search_market_data(query=query))
        result_message3 = SystemMessage(
               content=f"Firecrawl search_market_data:\n"
            )
        firecrawl_data.append(self.firecrawl.scrape_economic_data(indicator=query))
        result_message4 = SystemMessage(
               content=f"Firecrawl scrape_economic_data:\n"
            )
        result_message = SystemMessage(
            content=f"Firecrawl crawling results for query '{query}':\n{firecrawl_data}"
        )
        # Append the results to the state messages and then return the updated state.
        updated_messages = state["messages"] + [firecrawl_data, result_message3, result_message4]
        return {"messages": "good answer"} #updated_messages}

