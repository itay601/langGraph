from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from astrapy import DataAPIClient
from dotenv import load_dotenv 
from typing import List, Literal, Optional
from .workflow import Workflow_tradingAgent
from datetime import datetime

load_dotenv()


def get_user_emails():
    ASTRA_TOKEN = os.environ["ASTRA_TOKEN"]
    ASTRA_ENDPOINT = os.environ["ASTRA_ENDPOINT"]

    # Init Astra DB client
    client = DataAPIClient(ASTRA_TOKEN)
    db = client.get_database_by_api_endpoint(ASTRA_ENDPOINT)
    try:
        # Collection name
        TRADING_COLLECTION = "trading_bot"
        collection = db.get_collection(TRADING_COLLECTION)
        user_emails = [doc["user_email"] for doc in collection.find({})]
        return user_emails, collection
    except Exception as e:
        print(f"Error fetching user emails: {e}")
        return []


def cronjob_trading_agents():
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 
    llm = init_chat_model("google_genai:gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY)
    user_emails, collection = get_user_emails()
    for user_email in user_emails:
        user_prefs = collection.find_one({"user_email": user_email})
        #print(f"User Email: {user_email}, Preferences: {user_prefs_scheme}, Type: {type(user_prefs_scheme)}")
        
        workflow = Workflow_tradingAgent(llm, user_email, user_prefs)
        print("Economic & Stocks Trading Agent")
        query = (f"Financial Query: {user_prefs}").strip()
        if query:
            state = workflow.workflow.invoke({
                "messages": [{"role": "user", "content": query}],
                "user_preferences": user_prefs
            })
            invest_analysis = state.get("invest_analysis", {})
            if invest_analysis:
                collection.update_one(
                    {"user_email": user_email},
                    {"$set": {"invest_analysis": invest_analysis, "timestamp": datetime.utcnow().isoformat()}}
                )
            #data_fetched = state.get("data_fetched", {})
            #if data_fetched:
            #    collection.update_one(
            #        {"user_email": user_email},
            #        {"$set": {"data_fetched": data_fetched, "timestamp": datetime.utcnow().isoformat()}}
            #    )   # 