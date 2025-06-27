from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

from .workflow import Workflow
from dotenv import load_dotenv 

load_dotenv()




def get_chatbot_response():
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 
    llm = init_chat_model("google_genai:gemini-2.0-flash-exp",api_key=GOOGLE_API_KEY)

    workflow = Workflow(llm)
    print("Developer Tools Research Agent")


    query = input("\n🔍 Developer Tools Query: ").strip()
    if query:
        result = workflow.run(query)
        print(f"\n📊 Results for: {query}")
        print("=" * 60)

        for i, company in enumerate(result.companies, 1):
            print(f"\n{i}. 🏢 {company.name}")
            print(f"   🌐 Website: {company.website}")
            print(f"   💰 Pricing: {company.pricing_model}")
            print(f"   📖 Open Source: {company.is_open_source}")

            if company.tech_stack:
                print(f"   🛠️  Tech Stack: {', '.join(company.tech_stack[:5])}")

            if company.language_support:
                print(
                    f"   💻 Language Support: {', '.join(company.language_support[:5])}"
                )

            if company.api_available is not None:
                api_status = (
                    "✅ Available" if company.api_available else "❌ Not Available"
                )
                print(f"   🔌 API: {api_status}")

            if company.integration_capabilities:
                print(
                    f"   🔗 Integrations: {', '.join(company.integration_capabilities[:4])}"
                )

            if company.description and company.description != "Analysis failed":
                print(f"   📝 Description: {company.description}")

            print()

        if result.analysis:
            print("Developer Recommendations: ")
            print("-" * 40)
            print(result.analysis)            


