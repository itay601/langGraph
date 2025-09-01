from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END, add_messages
from typing_extensions import TypedDict
import astrapy
from dotenv import load_dotenv 
from typing import List, Literal, Optional
from .tools import get_reddit_vibe, get_stock_data_yahoo, get_ticker_data_poly, fetch_stock_price_polygon, get_related_articles, tools_list ,extract_symbols ,extract_symbols_list ,get_user_portfolio_from_astra,build_user_portfolio_from_astra
import re
import json
import datetime
from datetime import timedelta,datetime
from zoneinfo import ZoneInfo


load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]
    data_fetched: Optional[dict]
    invest_analysis: Optional[dict]
    #execution_plan : Optional[list]
    #decision_summary: Optional[dict]
    
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
        graph.add_node("investment_analysis", self._investment_analysis_node)        
        
        graph.add_edge(START,"market_research")
        graph.add_edge("market_research", "investment_analysis")
        graph.add_edge("investment_analysis", END)
        return graph.compile()    

    # -------------------------------
    # 1) MARKET RESEARCH NODE
    # -------------------------------
    def _market_research_node(self, state: State):
        """
        Parse the provided FINAL TRADING PLAN OUTPUT, extract stock tickers,
        and collect research for those tickers using the available tools.
        """
        if not self.initial_plan_record or "response" not in self.initial_plan_record:
            return None  

        response_text = self.initial_plan_record["response"]
        # --- Extract tickers from stock_allocations ---
        try:
            tickers_pre = extract_symbols(response_text)
            tickers = extract_symbols_list(tickers_pre)
        except Exception as e:
            tickers = []
               
        # --- Collect research for each ticker using your tools ---
        research_results = []
        for ticker in tickers:
            try:
                reddit_sentiment = get_reddit_vibe.invoke(ticker)
                yahoo_data = get_stock_data_yahoo(ticker)
                polygon_data = get_ticker_data_poly.invoke(ticker)
                latest_price = fetch_stock_price_polygon.invoke(ticker)
                news_articles = get_related_articles.invoke(ticker)
                
                #validate = build_user_portfolio_from_astra(
                #    self.user_emails,
                #    ticker,
                #    latest_price,
                #    yahoo_data,
                #    polygon_data,
                #    reddit_sentiment,
                #    news_articles,
                #    datetime.utcnow().isoformat()
                #)
                #print(f"Portfolio validated: {validate}")

                research_results.append({
                    "ticker": ticker,
                    "reddit_sentiment": reddit_sentiment,
                    "yahoo_data": yahoo_data,
                    "polygon_data": polygon_data,
                    "latest_price": latest_price,
                    "articles": news_articles,
                })
            except Exception as e:
                research_results.append({
                    "ticker": ticker,
                    "error": str(e)
                })
        state["data_fetched"] = research_results
        try:
            save_result = save_research_data_to_astra.invoke({
                "user_email": self.user_emails,
                "research_results": state["data_fetched"]
            })
        except Exception as e:
            return state
        return state


    # -------------------------------
    # 2) INVESTMENT ANALYSIS NODE
    # -------------------------------
    def _investment_analysis_node(self, state: State):
        """
        Analyze the current performance of the user's investments based on
        initial allocations vs. latest market data. 
        Calculates profit/loss per stock and overall portfolio performance.
        """
        if not self.initial_plan_record or "response" not in self.initial_plan_record:
            return state
        if "user_preferences" not in self.initial_plan_record:
            return state
            
        # Parse JSON from plan response
        try:
            response_text = self.initial_plan_record["response"]
            plan_json = re.search(r"FINAL TRADING PLAN OUTPUT:\s*(\{.*\})", response_text, re.S)
            if not plan_json:
                return state
            plan_data = json.loads(plan_json.group(1))
            allocations = plan_data["execution_summary"]["stock_allocations"]
        except Exception as e:
            return state

        # Get fetched market data from previous node
        research_results = state.get("data_fetched", [])
        ticker_to_price = {
            r["ticker"]: r.get("latest_price", {}).get("price") if isinstance(r.get("latest_price"), dict) else r.get("latest_price")
            for r in research_results
            if "ticker" in r
        }

        # Build investment analysis
        portfolio_analysis = []
        total_invested = 0
        total_value_invested = 0
        total_pnl_pct = 0

        for alloc in allocations:
            ticker = alloc["symbol"].split("-")[0]  # e.g. "BTC-USD" -> "BTC"
            reasoning = alloc.get("reasoning", "")

            shares = alloc.get("shares", 0)
            invested = alloc.get("allocated_amount", 0)
            
            price_now = ticker_to_price.get(ticker)

            if price_now is None:
                portfolio_analysis.append({
                    "ticker": ticker,
                    "status": "⚠️ No price data",
                    "invested": invested,
                    "shares": 0,
                    "reasoning" : reasoning
                })
                price_now = 0
                continue

            value_invested = alloc.get("allocated_amount", 0)
            share = float( value_invested / price_now) if price_now > 0 else 0
            
            date_status = datetime.now().isoformat()
            portfolio_analysis.append({
                "ticker": ticker,
                "invested": round(invested, 2),
                "shares": share,
                "price_bought": round(value_invested / share, 2) if share > 0 else 0,
                "price_now": price_now,
                "pnl": 0,
                "pnl_pct": 0,
                "date_status": date_status 
            })

            total_invested = total_invested + invested
            total_value_invested = total_value_invested + value_invested
            total_pnl_pct = 0

        portfolio_summary = {
            "total_invested": total_invested,
            "total_value_invested": total_value_invested,
            "total_pnl_pct": total_pnl_pct ,
            "portfolio_analysis": portfolio_analysis,
            "budget_remaining": self.initial_plan_record["user_preferences"]["budget"] - total_invested              
        }

        state["invest_analysis"] = {
            "summary": portfolio_summary
        }
        try:
            save_result = save_portfolio_data_to_astra.invoke({
                "user_email": self.user_emails,
                "portfolio_data": state.get("invest_analysis", {}),
                "state_data": state
            })
        except Exception as e:
            return state
        return state