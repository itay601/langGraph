from fastapi import FastAPI
from purpose.chatbot.chatbot import get_chatbot_response
from purpose.chatbot.models import ChatRequest, ChatResponse

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = get_chatbot_response(req.message)
    #return {"response": reply}
    return ChatResponse(response=reply)

@app.get("/")
def root():
    return {"msg":"server is running"}    

@app.get("/health")
def root():
    return {"msg":"server is healthy"}     