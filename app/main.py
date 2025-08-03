from fastapi import FastAPI
from chatbot.chatbot import get_chatbot_response
from multiAgent.tools import ArxivToAstra
from chatbot.models import ChatRequest, ChatRequest2, ChatResponse , FirecrawlInput ,UserChatHistory
from multiAgent.multiAgent import get_chat_response
from dotenv import load_dotenv 
import os
from datetime import datetime
from nvidiaModel.chatbot import nvidia_model
app = FastAPI()

@app.get("/chatbot")
def root():
    return {"msg":"server is running"}    

@app.get("/chatbot/health")
def health():
    return {"msg":"server is healthy"}     


@app.post("/chatbot/chatbotGemenai", response_model=ChatResponse)
async def chat(req: ChatRequest2):
    load_dotenv()
    ASTRA_TOKEN = os.environ["ASTRA_TOKEN"] 
    ASTRA_ENDPOINT = os.environ["ASTRA_ENDPOINT"] 

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
    #print(f"\n\nComplete response: {model_answer}")  
    #return ChatResponse(model_answer)
    return {"response": model_answer}
