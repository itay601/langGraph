from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

from .workflow import Workflow
from dotenv import load_dotenv 

load_dotenv()




def get_analysis_response(message: str):
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] 
    llm = init_chat_model("google_genai:gemini-2.0-flash-exp",api_key=GOOGLE_API_KEY)

    workflow = Workflow(llm)
    print("Economic & Stocks Research Agent")
    print("=" * 40)
    print("Ask about stocks, economic indicators, financial tools, or market analysis!")


    query = (f"Financial Query: {message}").strip()
    #query = row_input("\n📈 Financial Query: ").strip()
    if query:
        result , summary = workflow.run(query)
        print(f"\n📊 Financial Analysis for: {query}")
        print("=" * 60)

        for i, company in enumerate(result.companies, 1):
            print(f"\n{i}. 🏢 {company.name}")
            print(f"   🌐 Website: {company.website}")
            print(f"   💰 Pricing: {company.pricing_model}")
            print(f"   📊 Data Source: {company.is_data_provider}")

            if company.financial_metrics:
                    print(f"   📈 Financial Metrics: {', '.join(company.financial_metrics[:5])}")

            if company.market_coverage:
                print(f"   🌍 Market Coverage: {', '.join(company.market_coverage[:5])}")

            if company.api_available is not None:
                api_status = (
                    "✅ Available" if company.api_available else "❌ Not Available"
                )
                print(f"   🔌 API Access: {api_status}")

            if company.integration_platforms:
                print(f"   🔗 Integrations: {', '.join(company.integration_platforms[:4])}")

            if company.description and company.description != "Analysis failed":
                print(f"   📝 Description: {company.description}")

            if company.real_time_data is not None:
                real_time_status = "✅ Real-time" if company.real_time_data else "⏰ Delayed"
                print(f"   ⚡ Data Feed: {real_time_status}")

            print()

        if result.analysis:
            print("📋 Financial Recommendations:")
            print("-" * 40)
            print(result.analysis)   
              
        return summary   


