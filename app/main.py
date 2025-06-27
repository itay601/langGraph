from fastapi import FastAPI
from chatbot.chatbot import get_chatbot_response
from chatbot.models import ChatRequest, ChatResponse
#from chatbotWithTools.+++ import
#from chatbotWithTools.+++ import

app = FastAPI()

@app.get("/")
def root():
    return {"msg":"server is running"}    

@app.get("/health")
def root():
    return {"msg":"server is healthy"}     

@app.post("/chatbot", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = get_chatbot_response(req.message)
    #return {"response": reply}
    return ChatResponse(response=reply)

@app.post("/chatbottools", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = get_chatbot_response(req.message)
    #return {"response": reply}
    return ChatResponse(response=reply)