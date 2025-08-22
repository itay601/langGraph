from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from .workflow import Workflow
from dotenv import load_dotenv 
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
##############################
#workflow trading bot
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)
################
def trading_bot_multi_agents(user_prefs: UserPreferences):
    load_dotenv()
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 
    llm = init_chat_model("google_genai:gemini-2.5-flash", api_key=GOOGLE_API_KEY)
    #workflow = Workflow(llm, user_prefs)
    print("Economic & Stocks Research Agent")
    print("=" * 40)
    #query = (f"Financial Query: {message}").strip()
    #if query:
    #    state = workflow.workflow.invoke({
    #        "messages": [{"role": "user", "content": query}],
    #        "user_preferences": user_prefs.dict()
    #    })
    #    return state["messages"][-1].content

    #return None    