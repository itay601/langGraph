
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from tradingAgent.core.tools import get_ticker_data_poly, get_stock_data_yahoo, get_reddit_vibe, get_related_articles, save_portfolio_to_astra, get_user_portfolio_from_astra, tools_list
import logging
import json
import random
from datetime import datetime
import re, ast

logging.basicConfig(level=logging.INFO)

class TradingAgents:
    def __init__(self, llm, user_prefs):
        self.llm = llm.bind_tools(tools_list)
        self.user_prefs = user_prefs
        

    def chatbot(self, state):
        try:
            user_prefs = state.get("user_preferences", {})
            query = user_prefs.get("query", "")
            budget = user_prefs.get("budget", 0)
            strategy = user_prefs.get("strategy", "swing")
            preferred_markets = user_prefs.get("preferred_markets", ["stocks"])
            sanctions = user_prefs.get("sanctions", [])
            risk = user_prefs.get("risk", "medium")
            mode = user_prefs.get("mode", "virtual")

            # Agent generates stock list based on user preferences
            stock_list = []
            if preferred_markets and "stocks" in preferred_markets:
                try:
                    # Use query if provided, else use user preferences for suggestion
                    ticker_query = query if query else " ".join(preferred_markets)
                    # Use LLM to generate a diversified stock list prompt
                    llm_prompt = (
                        f"Generate a Python list of 10 stock ticker symbols relevant to '{ticker_query}'. "
                        f"Return ONLY the Python list, more then 20 companies."
                    )
                    llm_response = self.llm.invoke([HumanMessage(content=llm_prompt)])
                    logging.info(f"LLM response for ticker suggestion: {llm_response.content}, llm_response: {llm_response}")
                    raw_content = llm_response.content.strip()
                    # Remove ```python ... ``` if present
                    if raw_content.startswith("```"):
                        raw_content = re.sub(r"^```[a-zA-Z]*\n", "", raw_content)
                        raw_content = raw_content.rstrip("`").strip()

                    try:
                        tickers_result = {"tickers": ast.literal_eval(raw_content)}
                    except Exception:
                        tickers_result = {"tickers": []}
                    # Try to extract tickers from LLM response
                    try:
                        # If LLM returns a string representation of a list, safely evaluate it
                        tickers_result = {"tickers": ast.literal_eval(llm_response.content)}
                    except Exception:
                        tickers_result = {"tickers": []}
                    if tickers_result and isinstance(tickers_result, dict):
                        stock_list = tickers_result.get("tickers", [])
                    if not stock_list:
                        tickers_result = get_ticker_data_poly.invoke({"ticker": ticker_query})
                        if tickers_result and isinstance(tickers_result, dict):
                            stock_list = tickers_result.get("tickers", [])
                    if not stock_list:
                        # Fallback to default list if tools return nothing
                        stock_list = ["AAPL", "MSFT", "GOOGL"]
                except Exception as tool_error:
                    logging.warning(f"Tool error for ticker suggestion: {tool_error}")
                    stock_list = ["AAPL", "MSFT", "GOOGL"]
            else:
                stock_list = ["AAPL", "MSFT", "GOOGL"]

            # Filter out stocks based on sanctions or other constraints
            if sanctions:
                stock_list = [s for s in stock_list if s not in sanctions]

            # Limit number of stocks for simplicity
            stock_list = stock_list[:5] if len(stock_list) > 5 else stock_list

            # Generate actions and reasoning
            actions = {}
            for stock in stock_list:
                if risk == "low":
                    actions[stock] = {"action": "buy", "confidence": 0.7, "reasoning": "Conservative buy for stable growth"}
                elif risk == "high":
                    actions[stock] = {"action": "buy", "confidence": 0.9, "reasoning": "Aggressive buy for high returns"}
                else:  # medium
                    actions[stock] = {"action": "buy", "confidence": 0.8, "reasoning": "Moderate buy with balanced risk"}

            reasoning = f"Selected {len(stock_list)} stocks based on user preferences ({preferred_markets}), risk tolerance ({risk}), and budget (${budget})."

            # Create signals for portfolio manager
            signals = {}
            for stock, action_data in actions.items():
                signals[stock] = {
                    "action": action_data["action"],
                    "confidence": action_data["confidence"],
                    "reasoning": action_data["reasoning"]
                }

            summary = {
                "user_preferences": user_prefs,
                "stock_list": stock_list,
                "actions": actions,
                "reasoning": reasoning,
                "signals": signals
            }

            message = HumanMessage(
                content=f"🤖 Trading agent completed analysis!\n"
                        f"Strategy: {strategy}\n"
                        f"Suggested stocks: {', '.join(stock_list) if stock_list else 'None'}\n"
                        f"Actions: {json.dumps(actions, indent=2)}\n"
                        f"Reasoning: {reasoning}"
            )

            # Update state with signals for next agent
            state.update({
                "signals": signals,
                "symbols": stock_list,
                "strategy": strategy
            })

            return {"messages": [message], "summary": summary}
            
        except Exception as e:
            logging.error(f"Chatbot error: {str(e)}")
            error_message = SystemMessage(content=f"❌ Chatbot error: {str(e)}")
            return {"messages": [error_message]}


    def portfolio_manager_agent(self, state):
            try:
                signals = state.get("signals", {})
                user_prefs = state.get("user_preferences", {})
                budget = user_prefs.get("budget", 0)
                strategy = state.get("strategy", "swing")

                logging.info(f"Managing portfolio allocation for budget: ${budget}")

                portfolio_allocation = {}
                orders = []

                # Filter signals for actionable trades
                actionable_signals = {k: v for k, v in signals.items()
                                    if v.get("action") in ["buy", "sell"]}

                if actionable_signals and budget > 0:
                    num_positions = len(actionable_signals)
                    total_confidence = sum(signal.get("confidence", 1) for signal in actionable_signals.values())

                    for symbol, signal in actionable_signals.items():
                        confidence = signal.get("confidence", 1)
                        confidence_weight = confidence / total_confidence if total_confidence > 0 else 1 / num_positions
                        allocated_amount = budget * confidence_weight * 0.8  # Use 80%, keep 20% cash

                        # ✅ Use real stock price if available
                        try:
                            price_data = get_stock_data_yahoo.invoke({"ticker": symbol})
                            estimated_price = price_data.get("price", 100)
                        except Exception:
                            estimated_price = 100  # fallback

                        shares = int(allocated_amount / estimated_price)

                        # ✅ Always record allocation (even if 0 shares)
                        portfolio_allocation[symbol] = {
                            "symbol": symbol,
                            "action": signal.get("action"),
                            "allocated_amount": allocated_amount,
                            "confidence_weight": confidence_weight,
                            "position_size_shares": shares,
                            "estimated_price": estimated_price,
                            "portfolio_weight": confidence_weight,
                            "confidence": signal["confidence"],
                            "reasoning": signal.get("reasoning", "")
                        }

                        # ✅ Only add real orders if shares > 0
                        if shares > 0:
                            orders.append({
                                "symbol": symbol,
                                "action": signal["action"],
                                "quantity": shares,
                                "estimated_price": estimated_price,
                                "estimated_value": shares * estimated_price,
                                "order_type": "market",
                                "confidence": signal["confidence"]
                            })

                total_allocated = sum(alloc["allocated_amount"] for alloc in portfolio_allocation.values())
                cash_reserve = budget - total_allocated

                # Create execution plan
                execution_plan = {
                    "orders": orders,
                    "total_orders": len(orders),
                    "total_estimated_value": sum(order.get("estimated_value", 0) for order in orders),
                    "cash_reserve": cash_reserve,
                    "approved": True if portfolio_allocation else False,
                    "mode": user_prefs.get("mode", "virtual"),
                    "strategy": strategy,
                    "created_at": str(datetime.now())
                }

                message = SystemMessage(
                    content=f"💼 Portfolio allocation and execution plan ready\n"
                            f"Total budget: ${budget:,.2f}\n"
                            f"Allocated: ${total_allocated:,.2f}\n"
                            f"Cash reserve: ${cash_reserve:,.2f}\n"
                            f"Orders: {len(orders)}\n"
                            f"Mode: {execution_plan['mode']}\n"
                            f"Plan approved: {execution_plan['approved']}"
                )

                # Update state
                state.update({
                    "portfolio_allocation": portfolio_allocation,
                    "execution_plan": execution_plan
                })

                return {
                    "messages": [message],
                    "portfolio_allocation": portfolio_allocation,
                    "execution_plan": execution_plan
                }

            except Exception as e:
                logging.error(f"Portfolio manager error: {str(e)}")
                error_message = SystemMessage(content=f"❌ Portfolio manager error: {str(e)}")
                return {"messages": [error_message]}

    def action_executor_agent(self, state):
            try:
                execution_plan = state.get("execution_plan", {})
                user_prefs = state.get("user_preferences", {})
                portfolio_allocation = state.get("portfolio_allocation", {})

                # Get user email
                user_email = user_prefs.get("user_email") or getattr(self.user_prefs, "user_email", None)
                if not user_email:
                    user_email = "unknown_user@example.com"

                logging.info(f"Executing plan for user: {user_email}")

                # ✅ Save even if there are 0 orders (as long as we have a plan or allocation)
                if not portfolio_allocation and not execution_plan:
                    message = SystemMessage(
                        content="⚠️ No portfolio allocation or execution plan to save."
                    )
                    return {
                        "messages": [message],
                        "db_result": "No data to save",
                        "report_sent": False,
                        "summary_report": {}
                    }

                try:
                    portfolio_data = {
                        "portfolio_allocation": portfolio_allocation,
                        "execution_plan": execution_plan,
                        "user_preferences": user_prefs,
                        "timestamp": str(datetime.now())
                    }

                    db_result = save_portfolio_to_astra.invoke({
                        "user_email": user_email,
                        "portfolio_data": portfolio_data
                    })

                except Exception as db_error:
                    logging.error(f"Database save error: {str(db_error)}")
                    db_result = f"Database save failed: {str(db_error)}"

                # Retrieve from DB for confirmation
                try:
                    portfolio_from_db = get_user_portfolio_from_astra.invoke({
                        "user_email": user_email
                    })
                except Exception as db_error:
                    logging.error(f"Database retrieve error: {str(db_error)}")
                    portfolio_from_db = f"Database retrieve failed: {str(db_error)}"

                # Prepare summary
                summary_report = {
                    "user": user_email,
                    "execution_plan": execution_plan,
                    "portfolio_allocation": portfolio_allocation,
                    "portfolio_from_db": portfolio_from_db,
                    "timestamp": str(datetime.now())
                }

                def send_report(report, user):
                    logging.info(f"Sending summary report to {user}.")
                    return True

                report_sent = send_report(summary_report, user_email)

                message = SystemMessage(
                    content=f"✅ Action Executor: Plan executed.\n"
                            f"User: {user_email}\n"
                            f"Portfolio items: {len(portfolio_allocation)}\n"
                            f"Orders: {len(execution_plan.get('orders', []))}\n"
                            f"DB Save: {'Success' if 'failed' not in str(db_result) else 'Failed'}\n"
                            f"Report sent: {report_sent}"
                )

                return {
                    "messages": [message],
                    "db_result": db_result,
                    "report_sent": report_sent,
                    "summary_report": summary_report
                }

            except Exception as e:
                logging.error(f"Action Executor error: {str(e)}")
                error_message = SystemMessage(content=f"❌ Action Executor error: {str(e)}")
                return {"messages": [error_message], "db_result": None, "report_sent": False}