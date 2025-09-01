from fastapi import FastAPI
from chatbot.chatbot import get_chatbot_response
from multiAgent.tools import ArxivToAstra
from chatbot.models import ChatRequest, ChatRequest2, ChatResponse , FirecrawlInput ,UserChatHistory
from multiAgent.multiAgent import get_chat_response
from dotenv import load_dotenv 
import os
from datetime import datetime
from nvidiaModel.chatbot import nvidia_model
from tradingAgent.core.models import UserPreferences
from tradingAgent.main import trading_bot_multi_agents
from tradingAgent_cronjob.main import cronjob_trading_agents 
from astrapy import DataAPIClient
from langchain_core.messages import BaseMessage
import logging
import json

load_dotenv()
ASTRA_TOKEN = os.environ["ASTRA_TOKEN"] 
ASTRA_ENDPOINT = os.environ["ASTRA_ENDPOINT"] 

app = FastAPI()

@app.get("/chatbot")
def root():
    return {"msg":"server is running"}    

@app.get("/chatbot/health")
def health():
    return {"msg":"server is healthy"}     


@app.post("/chatbot/chatbotGemenai", response_model=ChatResponse)
async def chat(req: ChatRequest2):
    arxiv_store = ArxivToAstra(ASTRA_TOKEN, ASTRA_ENDPOINT)
    collection = arxiv_store.db.get_collection("users_queries_history")

    # Fetch user chat history 
    user_history = collection.find_one({"user_id": req.user_id})
    past_queries = []
    if user_history:
        past_queries = user_history.get("queries", [])[-5:]  # Get last 5 queries
    else:
        collection.insert_one({"user_id": req.user_id, "queries": []})

    context = "\n".join([q["query"] for q in past_queries])
    enriched_input = f"Context from past queries:\n{context}\n\nCurrent query: {req.message}"

    reply = get_chatbot_response(enriched_input)

    new_query = {"query": req.message, "timestamp": datetime.utcnow().isoformat()}
    updated_queries_history = (past_queries + [new_query])[-5:]

    collection.update_one(
        {"user_id": req.user_id},
        {"$set": {"queries": updated_queries_history}},
        upsert=True
    )
    return ChatResponse(response=reply)


@app.post("/chatbot/anlasisysAgent", response_model=ChatResponse)
def multiAgent(req: FirecrawlInput):
    reply = get_chat_response(req.query, req.economic_term, req.symbol)
    return {"response": reply}


@app.post("/chatbot/chatbotNvidia", response_model=ChatResponse)
async def chat(req: ChatRequest):
    model_answer = nvidia_model(req.message)        
    return {"response": model_answer}


def serialize_state(state: dict):
    serialized = {}
    for k, v in state.items():
        if isinstance(v, list) and all(isinstance(m, BaseMessage) for m in v):
            serialized[k] = [m.dict() for m in v]  
        else:
            try:
                _ = v.__dict__  
                serialized[k] = v.__dict__
            except:
                serialized[k] = v
    return serialized



@app.post("/chatbot/userTradingAgents", response_model=ChatResponse)
async def user_trading_bot(req: UserPreferences):
    try:
        client = DataAPIClient(ASTRA_TOKEN)
        db = client.get_database_by_api_endpoint(ASTRA_ENDPOINT)
        collection = db.get_collection("trading_bot")
        
        if collection.find_one({"user_email": req.user_email}):
            return {"response": "Error: A trading bot session already exists for this email."}

        model_answer, state , res= trading_bot_multi_agents(req)

        #state_serialized = serialize_state(state)  
        #final_full_state = json.dumps(state_serialized, ensure_ascii=False, indent=4)  
            
        collection.insert_one({
        "user_email": req.user_email,
        "response": model_answer,
        "user_preferences": req.dict(),
        "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        model_answer = f"Error: {e}"
        print(f"Error: {e}")    
    return {"response": res}





@app.get("/chatbot/cronTradingAgents", response_model=ChatResponse)
async def cronjob_trading_bot():
    try:
        state = cronjob_trading_agents()
        model_answer = "Cronjob trading agents executed."
    except Exception as e:
        model_answer = f"Error: {e}"
        print(f"Error: {e}")    
    return {"response": model_answer}