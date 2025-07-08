from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str


class FirecrawlInput(BaseModel):
    query: str  # Example: Search query
    economic_term: str  # Example: "GDP"
    symbol: str  # Example: "TSL"