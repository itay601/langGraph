from typing import Annotated
import os
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END, add_messages
from typing_extensions import TypedDict
import astrapy
from dotenv import load_dotenv 
from typing import List, Literal, Optional
from .tools import get_reddit_vibe, get_stock_data_yahoo, get_ticker_data_poly, fetch_stock_price_polygon, get_related_articles, tools_list ,extract_symbols ,extract_symbols_list
import re
import json
import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

import logging
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # You can change this to INFO or ERROR as needed
    format='%(asctime)s - %(levelname)s - %(message)s'
)


load_dotenv()


class State(TypedDict):
    messages: Annotated[list, add_messages]
    data_fetched: Optional[dict]
    invest_analysis: Optional[dict]
    execution_plan : Optional[list]
    decision_summary: Optional[dict]
    
    

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
        #graph.add_node("execution_planning", self._execution_planning_node)        
        
        graph.add_edge(START,"market_research")
        graph.add_edge("market_research", "investment_analysis")
        #graph.add_edge("investment_analysis", "execution_planning")
        #graph.add_edge("execution_planning", END)
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
        logging.info("Running market research node (from FINAL TRADING PLAN OUTPUT)...")

        if not self.initial_plan_record or "response" not in self.initial_plan_record:
            return None  

        response_text = self.initial_plan_record["response"]
        # --- Extract tickers from stock_allocations ---
        try:
            tickers_pre = extract_symbols(response_text)
            tickers = extract_symbols_list(tickers_pre)
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
        #logging.debug(f"Research results: {json.dumps(research_results, indent=2)}")
        state["data_fetched"] = research_results
        logging.info("Market research node completed.")
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
        logging.info("Running investment analysis node...")
        
        if not self.initial_plan_record or "response" not in self.initial_plan_record:
            logging.warning("No initial plan record available.")
            return state
        if "user_preferences" not in self.initial_plan_record:
            logging.warning("user_preferences missing in initial plan record.")
            return state
        # Parse JSON from plan response
        try:
            response_text = self.initial_plan_record["response"]
            plan_json = re.search(r"FINAL TRADING PLAN OUTPUT:\s*(\{.*\})", response_text, re.S)
            if not plan_json:
                logging.error("Could not parse plan JSON from response.")
                return state
            plan_data = json.loads(plan_json.group(1))
            allocations = plan_data["execution_summary"]["stock_allocations"]
        except Exception as e:
            logging.exception(f"Error parsing plan allocations: {e}")
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
        total_current_value = 0

        for alloc in allocations:
            ticker = alloc["symbol"].split("-")[0]  # e.g. "BTC-USD" -> "BTC"
            shares = alloc.get("shares", 0)
            invested = alloc.get("allocated_amount", 0)
            price_now = ticker_to_price.get(ticker)

            if price_now is None:
                portfolio_analysis.append({
                    "ticker": ticker,
                    "status": "⚠️ No price data",
                    "invested": invested,
                    "shares": shares
                })
                continue

            current_value = shares * price_now
            pnl = current_value - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0
            date_status = self.initial_plan_record["timestamp"]
            
            portfolio_analysis.append({
                "ticker": ticker,
                "invested": invested,
                "shares": shares,
                "price_now": price_now,
                "current_value": current_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "date_status": date_status 
            })

            total_invested += invested
            total_current_value += current_value

        # Portfolio summary
        portfolio_summary = {
            "total_invested": total_invested,
            "total_current_value": total_current_value,
            "total_pnl": total_current_value - total_invested,
            "total_pnl_pct": ((total_current_value - total_invested) / total_invested * 100)
                              if total_invested > 0 else 0,
            "portfolio_analysis": portfolio_analysis,
            "budget_remaining": self.initial_plan_record["user_preferences"]["budget"] - total_invested              
        }

        #logging.debug(f"Portfolio analysis: {json.dumps(portfolio_analysis, indent=2)}")
        logging.debug(f"Portfolio summary: {json.dumps(portfolio_summary, indent=2)}")

        state["invest_analysis"] = {
            "summary": portfolio_summary
        }

        logging.info("Investment analysis node completed.")
        return state
       

    def _parse_ts(self, s: str) -> Optional[datetime]:
        """
        Accepts 'YYYY-MM-DDTHH:MM:SS.ssssss' or 'YYYY-MM-DD HH:MM:SS.ssssss'.
        Returns timezone-aware dt in Asia/Jerusalem or None.
        """
        if not s or not isinstance(s, str):
            return None
        s = s.strip()
        # Try common formats
        fmts = ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S")
        for f in fmts:
            try:
                dt = datetime.strptime(s, f)
                # Make tz-aware (assuming your timestamps are local wall clock; adjust if UTC)
                return dt.replace(tzinfo=ZoneInfo("Asia/Jerusalem"))
            except Exception:
                continue
        return None

    # ---------------------------------------
    # Helper: gatekeeper for your 4 prechecks
    # ---------------------------------------
    def _prechecks(self, state: State) -> tuple[bool, str]:
        """
        Returns (ok, reason). If ok==False, do not continue.
        Rules:
          1) If latest timestamp < 15 minutes, don't run the agent.
          2) invest_analysis must exist in state AND have date_status inside portfolio items.
          3) user_preferences must exist in initial_plan_record.
          4) All must be found.
        """
        # 1) Recency check: prefer top-level document timestamp; fallback to plan timestamp
        doc_ts = None
        top_ts = self.initial_plan_record.get("timestamp")
        # 3) user_preferences existence
        if not self.initial_plan_record.get("user_preferences"):
            return (False, "user_preferences missing in document.")
        if top_ts:
            doc_ts = self._parse_ts(top_ts)

        # try inside response JSON too
        plan_ts = None
        try:
            resp = self.initial_plan_record.get("response", "")
            m = re.search(r'"timestamp"\s*:\s*"([^"]+)"', resp)
            if m:
                plan_ts = self._parse_ts(m.group(1))
        except Exception:
            pass

        last_ts = doc_ts or plan_ts
        if last_ts:
            now = datetime.now(ZoneInfo("Asia/Jerusalem"))
            if now - last_ts < timedelta(minutes=15):
                return (False, f"Recent document (last_ts={last_ts.isoformat()}), < 15 minutes. Skipping agent.")

        # 2) invest_analysis presence & date_status
        inv = state.get("invest_analysis")
        if not inv or "summary" not in inv or "portfolio_analysis" not in inv["summary"]:
            return (False, "invest_analysis not found or missing summary/portfolio_analysis.")

        portfolio_items = inv["summary"]["portfolio_analysis"]
        if not isinstance(portfolio_items, list) or len(portfolio_items) == 0:
            return (False, "invest_analysis.portfolio_analysis is empty.")
        # ensure at least one has date_status
        if not any(isinstance(x, dict) and x.get("date_status") for x in portfolio_items):
            return (False, "invest_analysis items missing date_status.")

        

        # 4) All requirements found -> OK
        return (True, "All prechecks passed.")

    # -------------------------------
    # 3) EXECUTION PLANNING NODE
    # -------------------------------
    def _execution_planning_node(self, state: State):
        """
        Turn analysis + prefs into concrete actions.
        Produces: state["execution_plan"] and state["decision_summary"].
        """
        logging.info("Running execution planning node...")

        ok, reason = self._prechecks(state)
        if not ok:
            logging.warning(f"Prechecks failed: {reason}")
            state["execution_plan"] = []
            state["decision_summary"] = {"executed": False, "reason": reason}
            return state

        # Inputs
        inv = state["invest_analysis"]["summary"]
        allocations = inv.get("portfolio_analysis", [])
        budget_remaining = inv.get("budget_remaining", 0.0)

        prefs = self.initial_plan_record["user_preferences"]
        stop_loss = float(prefs.get("stop_loss", 5))
        take_profit = float(prefs.get("take_profit", 15))
        trade_freq = str(prefs.get("trade_frequency", "medium")).lower()
        preferred_markets = prefs.get("preferred_markets", ["stocks", "crypto"])
        total_budget = float(prefs.get("budget", 0.0))
        leverage = float(prefs.get("leverage", 1.0))

        # Slightly adjust thresholds for "low" frequency to avoid churn
        if trade_freq == "low":
            stop_loss -= 1.0  # tolerate a bit more drawdown before selling
            take_profit += 2.0  # aim for a slightly higher take profit

        # We’ll also need the initial plan’s intended allocations (for BUY sizing)
        try:
            response_text = self.initial_plan_record["response"]
            plan_json = re.search(r"FINAL TRADING PLAN OUTPUT:\s*(\{.*\})", response_text, re.S)
            plan_data = json.loads(plan_json.group(1))
            plan_allocs = plan_data["execution_summary"]["stock_allocations"]
            plan_alloc_map = {a["symbol"]: a for a in plan_allocs}
        except Exception as e:
            logging.exception("Falling back: could not parse original plan allocations; BUY sizing may be limited.")
            plan_alloc_map = {}

        actions = []
        used_cash = 0.0

        # Decide for each symbol
        for item in allocations:
            ticker = item.get("ticker")
            shares = float(item.get("shares", 0))
            invested = float(item.get("invested", 0))
            price_now = item.get("price_now")
            pnl_pct = item.get("pnl_pct")

            # Skip if no current price
            if price_now is None:
                actions.append({
                    "symbol": ticker, "action": "HOLD",
                    "reason": "No current price available; risk-managed hold."
                })
                continue

            # Determine market type (simple heuristic; you can replace with your own mapping)
            market_type = "crypto" if ticker and ticker.upper() in {"BTC","ETH","SOL","ADA","DOGE"} else "stocks"
            if market_type not in preferred_markets:
                actions.append({
                    "symbol": ticker, "action": "SKIP",
                    "reason": f"Skipped due to preferred_markets={preferred_markets}."
                })
                continue

            if shares > 0:
                # If invested is 0 (shouldn't happen), compute avg from research if you store it; else hold.
                if invested <= 0:
                    actions.append({
                        "symbol": ticker, "action": "HOLD",
                        "reason": "No invested cost basis available."
                    })
                    continue

                # Decision by thresholds
                if pnl_pct is not None and pnl_pct <= -abs(stop_loss):
                    actions.append({
                        "symbol": ticker, "action": "SELL",
                        "size": "ALL",
                        "est_value": shares * float(price_now),
                        "reason": f"Hit stop-loss ({pnl_pct:.2f}% <= -{abs(stop_loss)}%)."
                    })
                elif pnl_pct is not None and pnl_pct >= abs(take_profit):
                    actions.append({
                        "symbol": ticker, "action": "SELL",
                        "size": "ALL",
                        "est_value": shares * float(price_now),
                        "reason": f"Reached take-profit ({pnl_pct:.2f}% >= {abs(take_profit)}%)."
                    })
                else:
                    actions.append({
                        "symbol": ticker, "action": "HOLD",
                        "reason": f"Within thresholds (SL {stop_loss}%, TP {take_profit}%)."
                    })

            else:
                # No shares currently. Consider BUY if plan wanted an allocation.
                plan_target = plan_alloc_map.get(ticker)
                if not plan_target:
                    actions.append({
                        "symbol": ticker, "action": "HOLD",
                        "reason": "No target allocation found in plan."
                    })
                    continue

                target_amount = float(plan_target.get("allocated_amount", 0.0))
                # Constrain by remaining budget
                buy_amount = min(target_amount, max(0.0, budget_remaining - used_cash))
                if buy_amount <= 0:
                    actions.append({
                        "symbol": ticker, "action": "HOLD",
                        "reason": "No remaining budget to open new position."
                    })
                    continue

                # Compute qty (round down to whole shares for stocks; adapt if you allow fractional)
                qty = int(buy_amount / float(price_now)) if market_type == "stocks" else buy_amount / float(price_now)
                if qty <= 0:
                    actions.append({
                        "symbol": ticker, "action": "HOLD",
                        "reason": "Planned buy amount too small for current price."
                    })
                    continue

                used_cash += float(qty) * float(price_now)
                actions.append({
                    "symbol": ticker,
                    "action": "BUY",
                    "qty": qty,
                    "est_cost": float(qty) * float(price_now),
                    "reason": f"Follow plan target (allocated_amount={target_amount}).",
                })

        # Summaries
        total_buys = sum(1 for a in actions if a["action"] == "BUY")
        total_sells = sum(1 for a in actions if a["action"] == "SELL")
        total_holds = sum(1 for a in actions if a["action"] == "HOLD")

        state["execution_plan"] = actions
        state["decision_summary"] = {
            "executed": True,
            "totals": {
                "buys": total_buys,
                "sells": total_sells,
                "holds": total_holds,
                "cash_to_use": used_cash,
                "cash_remaining_est": max(0.0, budget_remaining - used_cash),
            },
            "notes": {
                "stop_loss_used": stop_loss,
                "take_profit_used": take_profit,
                "trade_frequency": trade_freq,
                "preferred_markets": preferred_markets,
                "leverage": leverage,
            }
        }

        logging.info("Execution planning node completed.")
        return state
    