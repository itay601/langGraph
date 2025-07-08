from langchain_core.tools import tool
import requests
from pydantic import BaseModel



@tool(description="Fetches the latest economic or stock-related articles.")
def fetch_articles_2() -> dict:
    url = "http://127.0.0.1:8000/graphql"
    payload = {
        "query": "query { articles { id title content } }"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return {"data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@tool(description="Fetches the latest economic or stock-related articles.")
def fetch_articles(economic_term, symbol) -> dict:
    url = f"http://localhost:8000/v1/api/dataagent?economic_term={economic_term}&symbol={symbol}"
    try:
        response = requests.post(url)
        response.raise_for_status()
        return {"data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

##
## TODO !!!!
##
@tool(description="FireCrawl for advance crawling websites related to the economic terms Query")
def crawling(economic_term, query: str) -> dict:
    return 0

@tool
# This is new! 
class Question(BaseModel):
    """Question to ask user."""
    content: str        

@tool
# This is new! 
class Done(BaseModel):
    """Analysis has been sent to the user."""
    done: bool

tools = [ 
    fetch_articles, 
    Question, 
    Done,
]