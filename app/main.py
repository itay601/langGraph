from fastapi import FastAPI
from chatbot.chatbot import get_chatbot_response
from chatbot.models import ChatRequest, ChatResponse , FirecrawlInput
from multiAgent.multiAgent import get_chat_response


app = FastAPI()

@app.get("/")
def root():
    return {"msg":"server is running"}    

@app.get("/health")
def health():
    return {"msg":"server is healthy"}     

@app.post("/chatbot", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = get_chatbot_response(req.message)
    #return {"response": reply}
    return ChatResponse(response=reply)


@app.post("/anlasisysAgent", response_model=ChatResponse)
def multiAgent(req: FirecrawlInput):
    reply = get_chat_response(req.query, req.economic_term, req.symbol)
    return {"response": reply}
       