from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END, add_messages
from typing_extensions import TypedDict
import astrapy
from dotenv import load_dotenv 
from typing import List, Literal, Optional
from .tools import get_reddit_vibe, get_stock_data_yahoo, get_ticker_data_poly, fetch_stock_price_polygon, get_related_articles, tools_list ,extract_symbols
import re
import json
import datetime


import logging
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # You can change this to INFO or ERROR as needed
    format='%(asctime)s - %(levelname)s - %(message)s'
)


load_dotenv()


class State(TypedDict):
    messages: Annotated[list, add_messages]
    data_fetched: Optional[bool]
    

class Workflow_tradingAgent:
    def __init__(self, llm, user_emails: str, initial_plan_record: Optional[dict] = None):
        self.llm = llm.bind_tools(tools_list)
        self.user_emails = user_emails
        self.initial_plan_record = initial_plan_record 
        self.workflow = self._build_workflow()
        

    def _build_workflow(self):
        """Build enhanced workflow with better structure"""
        graph = StateGraph(state_schema=State)
        
        graph.add_node("market_research", self._market_research_node)
        #graph.add_node("investment_analysis", self._investment_analysis_node)
        #graph.add_node("portfolio_optimization", self._portfolio_optimization_node)
        #graph.add_node("execution_planning", self._execution_planning_node)
        #graph.add_node("validation", self._validation_node)
        #graph.add_node("final_output", self._final_output_node)
        
        
        graph.add_edge(START,"market_research")
        #graph.add_edge("market_research", "investment_analysis")
        #graph.add_edge("investment_analysis", "portfolio_optimization")
        #graph.add_edge("portfolio_optimization", "execution_planning")
        #graph.add_edge("execution_planning", "validation")
        #graph.add_edge("validation", "final_output")
        #graph.add_edge("final_output", END)
        graph.add_edge("market_research", END)
        
        return graph.compile()    

    # -------------------------------
    # 1) MARKET RESEARCH NODE
    # -------------------------------
    def _market_research_node(self, state: State):
        """
        Parse the provided FINAL TRADING PLAN OUTPUT, extract stock tickers,
        and collect research for those tickers using the available tools.
        """
        logging.info("Running market research node (from FINAL TRADING PLAN OUTPUT)...")

        if not self.initial_plan_record or "response" not in self.initial_plan_record:
            return None  

        response_text = self.initial_plan_record["response"]

        # --- Extract tickers from stock_allocations ---
        try:
            tickers = extract_symbols(response_text)
            logging.debug(f"Extracted symbols: {tickers}")
        except Exception as e:
            logging.error(f"Error extracting symbols: {e}")
            tickers = []
               
        # --- Collect research for each ticker using your tools ---
        research_results = []
        for ticker in tickers:
            try:
                logging.debug(f"Fetching research for {ticker} ...")
                reddit_sentiment = get_reddit_vibe.invoke(ticker)
                yahoo_data = get_stock_data_yahoo(ticker)
                polygon_data = get_ticker_data_poly.invoke(ticker)
                latest_price = fetch_stock_price_polygon.invoke(ticker)
                news_articles = get_related_articles.invoke(ticker)

                research_results.append({
                    "ticker": ticker,
                    "reddit_sentiment": reddit_sentiment,
                    "yahoo_data": yahoo_data,
                    "polygon_data": polygon_data,
                    "latest_price": latest_price,
                    "articles": news_articles,
                })
            except Exception as e:
                logging.exception(f"Error collecting data for {ticker}: {e}")
                research_results.append({
                    "ticker": ticker,
                    "error": str(e)
                })
        logging.debug(f"Research results: {json.dumps(research_results, indent=2)}")
        state["data_fetched"] = research_results
        logging.info("Market research node completed.")
        return state


    #def _investment_analysis_node(self):        

    #def _portfolio_optimization_node(self):

    #def _execution_planning_node(self):

    #def _validation_node(self):

    #def _final_output_node(self):             