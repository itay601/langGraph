from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

from dotenv import load_dotenv 
load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 
NVIDIA_MODEL_KEY = os.environ["NVIDIA_MODEL_KEY"]

llm = init_chat_model("google_genai:gemini-2.0-flash-exp",api_key=GOOGLE_API_KEY)
#llm2 = init_chat_model("google_genai:gemini-2.5-flash",api_key=GOOGLE_API_KEY)
#llm3 = init_chat_model("nvidia/llama-3.1-nemotron-70b-instruct",api_key=NVIDIA_MODEL_KEY)


def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile()

def get_chatbot_response(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            return value["messages"][-1].content