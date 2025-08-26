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
        """Enhanced chatbot that generates structured investment plans using tools"""
        try:
            user_prefs = state.get("user_preferences", {})
            query = user_prefs.get("query", "")
            budget = user_prefs.get("budget", 0)
            strategy = user_prefs.get("strategy", "swing")
            preferred_markets = user_prefs.get("preferred_markets", ["stocks"])
            risk = user_prefs.get("risk", "medium")
            mode = user_prefs.get("mode", "virtual")

            # Create a comprehensive prompt for the LLM to use tools and generate structured output
            analysis_prompt = f"""
            You are a professional trading analyst. Analyze the market and create an investment plan.
            
            USER PREFERENCES:
            - Query/Interest: {query}
            - Budget: ${budget}
            - Risk Level: {risk}
            - Strategy: {strategy}
            - Preferred Markets: {preferred_markets}
            - Mode: {mode}
            
            TASK: Create a detailed investment plan following these steps:
            
            1. RESEARCH PHASE:
               - Use get_reddit_vibe tool to analyze market sentiment for "{query}"
               - Use get_stock_data_yahoo to get historical data for potential stocks
               - Use get_ticker_data_poly for recent price data
            
            2. ANALYSIS PHASE:
               - Based on the data gathered, identify 5-10 stocks that match the user's preferences
               - Consider risk level when selecting stocks
               - Factor in the chosen strategy ({strategy})
            
            3. OUTPUT PHASE:
               - Generate a JSON response with the following structure:
               
            {{
                "investment_plan": {{
                    "strategy": "{strategy}",
                    "total_budget": {budget},
                    "risk_level": "{risk}",
                    "selected_stocks": [
                        {{
                            "symbol": "STOCK_SYMBOL",
                            "company_name": "Company Name",
                            "allocation_percentage": 25.0,
                            "allocation_amount": 2500.0,
                            "estimated_shares": 25,
                            "current_price": 100.0,
                            "reasoning": "Why this stock fits the strategy",
                            "confidence_score": 8.5,
                            "target_price": 120.0,
                            "stop_loss": 90.0
                        }}
                    ],
                    "cash_reserve_percentage": 10.0,
                    "market_analysis": {{
                        "sentiment": "positive/negative/neutral",
                        "key_trends": ["trend1", "trend2"],
                        "risk_factors": ["risk1", "risk2"]
                    }},
                    "execution_timeline": "immediate/1-week/1-month",
                    "rebalance_frequency": "weekly/monthly/quarterly"
                }}
            }}
            
            IMPORTANT: 
            - Use the tools available to gather real market data
            - Make tool calls to get actual stock prices and sentiment
            - Ensure allocations add up to no more than 90% (keep 10% cash)
            - Match stock selection to risk level and strategy
            - Provide specific reasoning for each stock choice
            
            Start by making tool calls to gather data, then generate the final JSON response.
            """

            # Send the comprehensive prompt to LLM
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            
            # Log the response for debugging
            logging.info(f"LLM response: {response.content}")
            
            # Extract JSON from response if it's wrapped in markdown
            response_content = response.content.strip()
            if "```json" in response_content:
                # Extract JSON from markdown code block
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                # Extract JSON from code block
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            else:
                json_content = response_content
            
            try:
                # Parse the JSON response
                investment_plan = json.loads(json_content)
            except json.JSONDecodeError as e:
                logging.error(f"JSON parsing error: {e}")
                # Fallback: create a basic plan
                investment_plan = self._create_fallback_plan(user_prefs)

            # Extract data for next agents
            selected_stocks = investment_plan.get("investment_plan", {}).get("selected_stocks", [])
            stock_symbols = [stock["symbol"] for stock in selected_stocks]
            
            # Create signals for portfolio manager
            signals = {}
            for stock in selected_stocks:
                signals[stock["symbol"]] = {
                    "action": "buy",
                    "confidence": stock.get("confidence_score", 8.0) / 10.0,
                    "reasoning": stock.get("reasoning", "Selected based on analysis"),
                    "allocation_percentage": stock.get("allocation_percentage", 0),
                    "target_price": stock.get("target_price", 0),
                    "stop_loss": stock.get("stop_loss", 0)
                }

            # Create summary message
            summary_message = HumanMessage(
                content=f"🤖 Trading Analysis Complete!\n"
                        f"Strategy: {strategy}\n"
                        f"Selected {len(selected_stocks)} stocks: {', '.join(stock_symbols)}\n"
                        f"Total allocation: {sum(s.get('allocation_percentage', 0) for s in selected_stocks):.1f}%\n"
                        f"Investment Plan: {json.dumps(investment_plan, indent=2)}"
            )

            # Update state
            state.update({
                "signals": signals,
                "symbols": stock_symbols,
                "strategy": strategy,
                "investment_plan": investment_plan
            })

            return {
                "messages": [summary_message], 
                "investment_plan": investment_plan,
                "signals": signals
            }
            
        except Exception as e:
            logging.error(f"Chatbot error: {str(e)}")
            # Create fallback plan
            fallback_plan = self._create_fallback_plan(user_prefs)
            error_message = SystemMessage(
                content=f"❌ Analysis error, using fallback plan: {json.dumps(fallback_plan, indent=2)}"
            )
            return {
                "messages": [error_message],
                "investment_plan": fallback_plan,
                "signals": {}
            }

    def _create_fallback_plan(self, user_prefs):
        """Create a basic fallback investment plan"""
        budget = user_prefs.get("budget", 10000)
        risk = user_prefs.get("risk", "medium")
        strategy = user_prefs.get("strategy", "swing")
        
        # Default stocks based on risk level
        if risk == "low":
            default_stocks = [
                {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "allocation": 30},
                {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "allocation": 25},
                {"symbol": "AAPL", "name": "Apple Inc.", "allocation": 20},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "allocation": 15}
            ]
        elif risk == "high":
            default_stocks = [
                {"symbol": "TSLA", "name": "Tesla Inc.", "allocation": 25},
                {"symbol": "NVDA", "name": "NVIDIA Corporation", "allocation": 25},
                {"symbol": "AMD", "name": "Advanced Micro Devices", "allocation": 20},
                {"symbol": "PLTR", "name": "Palantir Technologies", "allocation": 20}
            ]
        else:  # medium
            default_stocks = [
                {"symbol": "AAPL", "name": "Apple Inc.", "allocation": 25},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "allocation": 25},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "allocation": 20},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "allocation": 20}
            ]
        
        selected_stocks = []
        for stock in default_stocks:
            allocation_amount = (budget * stock["allocation"] / 100)
            estimated_price = 150  # Rough estimate
            estimated_shares = int(allocation_amount / estimated_price)
            
            selected_stocks.append({
                "symbol": stock["symbol"],
                "company_name": stock["name"],
                "allocation_percentage": stock["allocation"],
                "allocation_amount": allocation_amount,
                "estimated_shares": estimated_shares,
                "current_price": estimated_price,
                "reasoning": f"Default selection for {risk} risk {strategy} strategy",
                "confidence_score": 7.0,
                "target_price": estimated_price * 1.2,
                "stop_loss": estimated_price * 0.9
            })
        
        return {
            "investment_plan": {
                "strategy": strategy,
                "total_budget": budget,
                "risk_level": risk,
                "selected_stocks": selected_stocks,
                "cash_reserve_percentage": 10.0,
                "market_analysis": {
                    "sentiment": "neutral",
                    "key_trends": ["Market uncertainty", "Tech growth"],
                    "risk_factors": ["Market volatility", "Economic uncertainty"]
                },
                "execution_timeline": "immediate",
                "rebalance_frequency": "monthly"
            }
        }

    def portfolio_manager_agent(self, state):
        """Enhanced portfolio manager that processes the investment plan"""
        try:
            investment_plan = state.get("investment_plan", {}).get("investment_plan", {})
            user_prefs = state.get("user_preferences", {})
            budget = investment_plan.get("total_budget", user_prefs.get("budget", 0))
            
            logging.info(f"Processing investment plan with budget: ${budget}")

            portfolio_allocation = {}
            orders = []
            
            selected_stocks = investment_plan.get("selected_stocks", [])
            
            for stock_data in selected_stocks:
                symbol = stock_data["symbol"]
                allocation_percentage = stock_data.get("allocation_percentage", 0)
                estimated_price = stock_data.get("current_price", 100)
                allocation_amount = stock_data.get("allocation_amount", 0)
                estimated_shares = stock_data.get("estimated_shares", 0)
                
                # Create portfolio allocation entry
                portfolio_allocation[symbol] = {
                    "symbol": symbol,
                    "company_name": stock_data.get("company_name", "Unknown"),
                    "action": "buy",
                    "allocation_percentage": allocation_percentage,
                    "allocated_amount": allocation_amount,
                    "position_size_shares": estimated_shares,
                    "estimated_price": estimated_price,
                    "confidence": stock_data.get("confidence_score", 8.0) / 10.0,
                    "reasoning": stock_data.get("reasoning", ""),
                    "target_price": stock_data.get("target_price", 0),
                    "stop_loss": stock_data.get("stop_loss", 0)
                }
                
                # Create order if shares > 0
                if estimated_shares > 0:
                    orders.append({
                        "symbol": symbol,
                        "action": "buy",
                        "quantity": estimated_shares,
                        "estimated_price": estimated_price,
                        "estimated_value": estimated_shares * estimated_price,
                        "order_type": "market",
                        "confidence": stock_data.get("confidence_score", 8.0) / 10.0
                    })

            total_allocated = sum(alloc["allocated_amount"] for alloc in portfolio_allocation.values())
            cash_reserve = budget - total_allocated

            # Create execution plan
            execution_plan = {
                "orders": orders,
                "total_orders": len(orders),
                "total_estimated_value": sum(order.get("estimated_value", 0) for order in orders),
                "cash_reserve": cash_reserve,
                "cash_reserve_percentage": (cash_reserve / budget * 100) if budget > 0 else 0,
                "approved": True if portfolio_allocation else False,
                "mode": user_prefs.get("mode", "virtual"),
                "strategy": investment_plan.get("strategy", "swing"),
                "execution_timeline": investment_plan.get("execution_timeline", "immediate"),
                "rebalance_frequency": investment_plan.get("rebalance_frequency", "monthly"),
                "created_at": str(datetime.now()),
                "market_analysis": investment_plan.get("market_analysis", {})
            }

            message = SystemMessage(
                content=f"💼 Portfolio Manager: Execution plan ready\n"
                        f"Total budget: ${budget:,.2f}\n"
                        f"Allocated: ${total_allocated:,.2f}\n"
                        f"Cash reserve: ${cash_reserve:,.2f} ({cash_reserve/budget*100:.1f}%)\n"
                        f"Orders: {len(orders)}\n"
                        f"Strategy: {execution_plan['strategy']}\n"
                        f"Timeline: {execution_plan['execution_timeline']}\n"
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
        """Enhanced action executor that saves structured data and provides detailed reporting"""
        try:
            execution_plan = state.get("execution_plan", {})
            portfolio_allocation = state.get("portfolio_allocation", {})
            investment_plan = state.get("investment_plan", {})
            user_prefs = state.get("user_preferences", {})

            # Get user email
            user_email = user_prefs.get("user_email") or getattr(self.user_prefs, "user_email", None)
            if not user_email:
                user_email = "unknown_user@example.com"

            logging.info(f"Executing plan for user: {user_email}")

            # Prepare comprehensive portfolio data for database
            portfolio_data = {
                "investment_plan": investment_plan,
                "portfolio_allocation": portfolio_allocation,
                "execution_plan": execution_plan,
                "user_preferences": user_prefs,
                "timestamp": str(datetime.now()),
                "status": "planned"  # planned, executed, monitoring, closed
            }

            # Save to database
            try:
                db_result = save_portfolio_to_astra.invoke({
                    "user_email": user_email,
                    "portfolio_data": portfolio_data
                })
            except Exception as db_error:
                logging.error(f"Database save error: {str(db_error)}")
                db_result = {"success": False, "error": str(db_error)}

            # Create detailed summary report
            summary_report = {
                "user": user_email,
                "plan_summary": {
                    "strategy": execution_plan.get("strategy", "Unknown"),
                    "total_budget": investment_plan.get("investment_plan", {}).get("total_budget", 0),
                    "stocks_count": len(portfolio_allocation),
                    "orders_count": len(execution_plan.get("orders", [])),
                    "cash_reserve_percentage": execution_plan.get("cash_reserve_percentage", 0),
                    "execution_timeline": execution_plan.get("execution_timeline", "immediate"),
                    "mode": execution_plan.get("mode", "virtual")
                },
                "stock_allocations": [
                    {
                        "symbol": symbol,
                        "allocation_percentage": data.get("allocation_percentage", 0),
                        "allocated_amount": data.get("allocated_amount", 0),
                        "shares": data.get("position_size_shares", 0),
                        "reasoning": data.get("reasoning", "")
                    }
                    for symbol, data in portfolio_allocation.items()
                ],
                "market_analysis": execution_plan.get("market_analysis", {}),
                "database_status": "success" if db_result.get("success") else "failed",
                "timestamp": str(datetime.now())
            }

            # Create final message with JSON output
            final_output = {
                "trading_plan_status": "completed",
                "execution_summary": summary_report,
                "next_steps": [
                    "Monitor market conditions",
                    "Execute orders according to timeline",
                    f"Rebalance {execution_plan.get('rebalance_frequency', 'monthly')}",
                    "Update stop-loss and target prices as needed"
                ]
            }

            message = SystemMessage(
                content=f"✅ Action Executor: Trading plan completed and saved!\n\n"
                        f"FINAL TRADING PLAN OUTPUT:\n"
                        f"{json.dumps(final_output, indent=2)}\n\n"
                        f"Database Status: {'✅ Saved' if db_result.get('success') else '❌ Save Failed'}\n"
                        f"Portfolio ID: {db_result.get('portfolio_id', 'N/A')}"
            )

            return {
                "messages": [message],
                "final_output": final_output,
                "db_result": db_result,
                "summary_report": summary_report
            }

        except Exception as e:
            logging.error(f"Action Executor error: {str(e)}")
            error_message = SystemMessage(content=f"❌ Action Executor error: {str(e)}")
            return {"messages": [error_message], "final_output": None}