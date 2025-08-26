from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from tradingAgent.agents.agents import Workflow_tradingAgent
from dotenv import load_dotenv 
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from utills.firecrawl import FirecrawlService
from tradingAgent.core.models import UserPreferences
import logging



# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # You can change this to INFO or ERROR as needed
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def trading_bot_multi_agents(user_prefs: UserPreferences):
    load_dotenv()
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 
    llm = init_chat_model("google_genai:gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY)
    workflow = Workflow_tradingAgent(llm, user_prefs, FirecrawlService)
    print("Economic & Stocks Trading Agent")
    print("=" * 40)
    query = (f"Financial Query: {user_prefs.query}").strip()
    if query:
        state = workflow.workflow.invoke({
            "messages": [{"role": "user", "content": query}],
            "user_preferences": user_prefs.dict()
        })
        
        return state["messages"][-1].content ,state
    return None    