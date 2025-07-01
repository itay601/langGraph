from typing import Dict, Any ,Annotated 
from langgraph.graph import StateGraph, END ,START
from langchain_core.messages import HumanMessage, SystemMessage
from utills.firecrawl import FirecrawlService
#from .promts import FinancialToolsPrompts
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from .tools import fetch_articles

class State(TypedDict):
    messages: Annotated[list, add_messages]

class Workflow:
    def __init__(self,llm):
        #self.firecrawl = FirecrawlService()
        self.llm = llm
        #self.prompts = FinancialToolsPrompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(State)
        graph.add_node("chatbot", self._chatbot)
        graph.add_node("fetch_articles" , fetch_articles) #tool
        #graph.set_entry_point("extract_financial_tools")
        graph.add_edge(START , "fetch_articles")
        graph.add_edge("fetch_articles" , "chatbot")
        graph.add_edge("chatbot", END)
        return graph.compile()

    def _chatbot(self, state: State):
        return {"messages": [self.llm.invoke(state["messages"])] }

