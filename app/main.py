from fastapi import FastAPI
from chatbot.chatbot import get_chatbot_response
from chatbot.models import ChatRequest, ChatResponse
from chatbotWithTools.chatWithTools import get_analysis_response
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

#not good enough need to think again about Structure of the Agent
@app.post("/chatbottools", response_model=ChatResponse)
def chatWithTools(req: ChatRequest):
    result = get_analysis_response(req.message)
    analysis_text = result.analysis if hasattr(result, 'analysis') else "No analysis available"
    return ChatResponse(response=analysis_text)
    #return ChatResponse(response=reply)

@app.post("/anlasisysAgent", response_model=ChatResponse)
def multiAgent(req: ChatRequest):
    reply = get_chat_response(req.message)
    return {"response": reply}
       