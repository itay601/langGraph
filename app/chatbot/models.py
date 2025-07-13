from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str


class FirecrawlInput(BaseModel):
    query: str  
    economic_term: str
    symbol: str  

class ChatRequest2(BaseModel):
    user_id: str
    message: str

class UserChatHistory(BaseModel):
    user_id: str
    queries: list[dict]      