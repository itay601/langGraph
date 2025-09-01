from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from astrapy import DataAPIClient
from dotenv import load_dotenv 
from typing import List, Literal, Optional
from .workflow import Workflow_tradingAgent
from datetime import datetime
import redis
import json
import pandas as pd
import numpy as np
from langgraph.pregel.io import AddableValuesDict


load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True,  
    username=os.getenv("REDIS_USERNAME", None)  
)

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


def set_state(user_email, state):
    key = f"user:{user_email}"
    redis_client.set(key, state)
    data = redis_client.get(key)
    return data

def get_state(user_email):
    key = f"user:{user_email}"
    data = redis_client.get(key)
    return json.loads(data) if data else None



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
            invest_analysis = state["invest_analysis"]
            if invest_analysis:
                collection.update_one(
                    {"user_email": user_email},
                    {"$set": {"invest_analysis": invest_analysis, "timestamp": datetime.utcnow().isoformat()}}
                )
            data_fetched = state["data_fetched"]
            print(f"Data fetched: {type(state)}")
            print(f"Data fetched: {type(dict(state))}")
            redis_data = dict(state)
            redis_data_str = json.dumps(redis_data, default=str)
            #print(f"Data fetched: {type(convert_state_for_redis(state))}")
            if data_fetched:
                res = set_state(user_email, redis_data_str)
            get_state(user_email)    
            return state["messages"][-1].content, state ,res    