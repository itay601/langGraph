from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from .workflow import Workflow
from dotenv import load_dotenv 

load_dotenv()




def get_chat_response(message: str):
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 
    llm = init_chat_model("google_genai:gemini-2.0-flash-exp",api_key=GOOGLE_API_KEY)
    workflow = Workflow(llm)
    print("Economic & Stocks Research Agent")
    print("=" * 40)
    
    query = (f"Financial Query: {message}").strip()
    #query = row_input("\n📈 Financial Query: ").strip()
    if query:
        state = workflow.workflow.invoke({"messages": [{"role":"user", "content":query}]})
        return state["messages"][-1].content

    return None    