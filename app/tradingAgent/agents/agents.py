from typing import Dict, Any, Annotated 
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, SystemMessage
from utills.firecrawl import FirecrawlService
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from tradingAgent.core.tools import tools_list
from .tradingAgents import TradingAgents
import logging
import json
from datetime import datetime

# Enhanced State with better structure
class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_preferences: dict
    query: str
    symbols: list[str]
    strategy: str
    market_analysis: dict
    investment_plan: dict
    execution_plan: dict
    portfolio_allocation: dict
    trade_results: dict
    validation_results: dict

class Workflow_tradingAgent:
    def __init__(self, llm, user_prefs, FirecrawlService):
        self.firecrawl = FirecrawlService()
        self.llm = llm.bind_tools(tools_list)
        self.user_prefs = user_prefs
        self.agents = TradingAgents(self.llm, user_prefs)
        self.workflow = self._build_workflow()
       
    def _build_workflow(self):
        """Build enhanced workflow with better structure"""
        graph = StateGraph(state_schema=State)

        graph.add_node("firecrawl_search", self._firecrawl_search)
        graph.add_node("market_research", self._market_research_node)
        graph.add_node("investment_analysis", self._investment_analysis_node)
        graph.add_node("portfolio_optimization", self._portfolio_optimization_node)
        graph.add_node("execution_planning", self._execution_planning_node)
        graph.add_node("validation", self._validation_node)
        graph.add_node("final_output", self._final_output_node)
        
        graph.add_edge(START, "firecrawl_search")
        graph.add_edge("firecrawl_search","market_research")
        graph.add_edge("market_research", "investment_analysis")
        graph.add_edge("investment_analysis", "portfolio_optimization")
        graph.add_edge("portfolio_optimization", "execution_planning")
        graph.add_edge("execution_planning", "validation")
        graph.add_edge("validation", "final_output")
        graph.add_edge("final_output", END)
        
        return graph.compile()

    def _market_research_node(self, state: State):
        """Dedicated market research using tools"""
        try:
            user_prefs = state.get("user_preferences", {})
            query = user_prefs.get("query", "financial market analysis")
            
            logging.info(f"Starting market research for: {query}")
            
            # Create focused research prompt
            research_prompt = f"""
            You are a market research analyst. Use the available tools to gather comprehensive market data.
            
            RESEARCH TOPIC: {query}
            
            MANDATORY TASKS:
            1. Use get_reddit_vibe("{query}") to analyze market sentiment
            2. Use get_related_articles("{query}") to get recent news
            3. Use stock data tools to analyze price trends
            
            After gathering data, provide a summary in this JSON format:
            {{
                "market_research": {{
                    "sentiment_analysis": {{
                        "overall_sentiment": "positive/negative/neutral",
                        "sentiment_score": 0.0,
                        "key_themes": ["theme1", "theme2"],
                        "reddit_insights": "Summary of Reddit sentiment"
                    }},
                    "news_analysis": {{
                        "recent_developments": ["news1", "news2"],
                        "market_catalysts": ["catalyst1", "catalyst2"],
                        "risk_events": ["risk1", "risk2"]
                    }},
                    "market_conditions": {{
                        "trend_direction": "bullish/bearish/sideways",
                        "volatility_level": "low/medium/high",
                        "market_phase": "accumulation/distribution/trending"
                    }}
                }}
            }}
            
            Use tools FIRST, then analyze the results. Return ONLY the JSON structure.
            """
            
            # Execute research
            response = self.llm.invoke([HumanMessage(content=research_prompt)])
            
            # Extract JSON from response
            market_analysis = self._extract_json_from_response(response.content, "market_research")
            
            message = SystemMessage(
                content=f"📊 Market Research Completed\n"
                        f"Query: {query}\n"
                        f"Analysis: {json.dumps(market_analysis, indent=2)}"
            )
            
            return {
                "messages": [message],
                "market_analysis": market_analysis
            }
            
        except Exception as e:
            logging.error(f"Market research error: {str(e)}")
            error_message = SystemMessage(content=f"❌ Market research error: {str(e)}")
            return {"messages": [error_message], "market_analysis": {}}

    def _investment_analysis_node(self, state: State):
        """Enhanced investment analysis with structured output"""
        try:
            user_prefs = state.get("user_preferences", {})
            market_analysis = state.get("market_analysis", {})
            
            logging.info("Starting investment analysis...")
            
            # Create comprehensive analysis prompt
            analysis_prompt = f"""
            You are a professional investment analyst. Generate a detailed investment plan.
            
            USER PREFERENCES:
            {json.dumps(user_prefs, indent=2)}
            
            MARKET ANALYSIS:
            {json.dumps(market_analysis, indent=2)}
            
            TASK: Create a complete investment plan using available tools for real data.
            
            STEPS:
            1. Use stock data tools to get current prices for potential stocks
            2. Analyze which stocks fit the user's criteria
            3. Calculate optimal allocations based on budget and risk level
            
            OUTPUT EXACTLY THIS JSON STRUCTURE:
            {{
                "investment_plan": {{
                    "status": "generated",
                    "timestamp": "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "strategy": "{user_prefs.get('strategy', 'swing')}",
                    "risk_level": "{user_prefs.get('risk', 'medium')}",
                    "total_budget": {user_prefs.get('budget', 0)},
                    "user_query": "{user_prefs.get('query', '')}",
                    "selected_stocks": [
                        {{
                            "symbol": "ACTUAL_TICKER",
                            "company_name": "Real Company Name",
                            "current_price": 150.00,
                            "allocation_percentage": 25.0,
                            "allocation_amount": 12500.0,
                            "shares_to_buy": 83,
                            "target_price": 180.00,
                            "stop_loss_price": 135.00,
                            "confidence_score": 8.5,
                            "reasoning": "Specific reason based on analysis and market data",
                            "expected_return": 20.0,
                            "time_horizon": "3-6 months"
                        }}
                    ],
                    "risk_management": {{
                        "cash_reserve_percentage": 10.0,
                        "max_position_size": 25.0,
                        "stop_loss_percentage": 10.0,
                        "rebalance_frequency": "monthly"
                    }}
                }}
            }}
            
            REQUIREMENTS:
            - Include 5-8 stocks maximum
            - Use REAL prices from tools
            - Ensure allocations sum to ≤ 90%
            - Calculate exact shares: allocation_amount ÷ current_price
            - Set realistic target and stop-loss prices
            - Provide specific reasoning for each stock
            
            Use tools to get real data, then return ONLY the JSON structure.
            """
            
            # Execute analysis
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            
            # Extract and validate JSON
            investment_plan = self._extract_json_from_response(response.content, "investment_plan")
            
            # Extract stock symbols for next steps
            selected_stocks = investment_plan.get("investment_plan", {}).get("selected_stocks", [])
            symbols = [stock.get("symbol") for stock in selected_stocks if stock.get("symbol")]
            
            message = SystemMessage(
                content=f"💡 Investment Analysis Complete\n"
                        f"Selected {len(selected_stocks)} stocks: {', '.join(symbols)}\n"
                        f"Total Budget: ${investment_plan.get('investment_plan', {}).get('total_budget', 0):,.2f}"
            )
            
            return {
                "messages": [message],
                "investment_plan": investment_plan,
                "symbols": symbols
            }
            
        except Exception as e:
            logging.error(f"Investment analysis error: {str(e)}")
            error_message = SystemMessage(content=f"❌ Investment analysis error: {str(e)}")
            return {"messages": [error_message], "investment_plan": {}}

    def _portfolio_optimization_node(self, state: State):
        """Optimize portfolio allocation and risk management"""
        try:
            investment_plan = state.get("investment_plan", {})
            user_prefs = state.get("user_preferences", {})
            
            logging.info("Optimizing portfolio allocation...")
            
            # Create portfolio allocation data structure
            plan_data = investment_plan.get("investment_plan", {})
            selected_stocks = plan_data.get("selected_stocks", [])
            
            portfolio_allocation = {}
            total_allocation = 0
            
            for stock in selected_stocks:
                symbol = stock.get("symbol")
                if symbol:
                    portfolio_allocation[symbol] = {
                        "symbol": symbol,
                        "company_name": stock.get("company_name", ""),
                        "action": "buy",
                        "allocation_percentage": stock.get("allocation_percentage", 0),
                        "allocated_amount": stock.get("allocation_amount", 0),
                        "position_size_shares": stock.get("shares_to_buy", 0),
                        "estimated_price": stock.get("current_price", 0),
                        "target_price": stock.get("target_price", 0),
                        "stop_loss": stock.get("stop_loss_price", 0),
                        "confidence": stock.get("confidence_score", 8.0) / 10.0,
                        "reasoning": stock.get("reasoning", ""),
                        "expected_return": stock.get("expected_return", 0),
                        "time_horizon": stock.get("time_horizon", "3-6 months")
                    }
                    total_allocation += stock.get("allocation_percentage", 0)
            
            # Validate and adjust allocations if needed
            if total_allocation > 90:
                logging.warning(f"Total allocation {total_allocation}% exceeds 90%, adjusting...")
                adjustment_factor = 90 / total_allocation
                for symbol in portfolio_allocation:
                    portfolio_allocation[symbol]["allocation_percentage"] *= adjustment_factor
                    portfolio_allocation[symbol]["allocated_amount"] *= adjustment_factor
                    
            cash_reserve = plan_data.get("total_budget", 0) * (100 - total_allocation) / 100
            
            message = SystemMessage(
                content=f"🎯 Portfolio Optimization Complete\n"
                        f"Total Positions: {len(portfolio_allocation)}\n"
                        f"Total Allocation: {total_allocation:.1f}%\n"
                        f"Cash Reserve: ${cash_reserve:,.2f}"
            )
            
            return {
                "messages": [message],
                "portfolio_allocation": portfolio_allocation
            }
            
        except Exception as e:
            logging.error(f"Portfolio optimization error: {str(e)}")
            error_message = SystemMessage(content=f"❌ Portfolio optimization error: {str(e)}")
            return {"messages": [error_message], "portfolio_allocation": {}}

    def _execution_planning_node(self, state: State):
        """Create detailed execution plan"""
        try:
            portfolio_allocation = state.get("portfolio_allocation", {})
            investment_plan = state.get("investment_plan", {})
            user_prefs = state.get("user_preferences", {})
            
            logging.info("Creating execution plan...")
            
            # Create orders list
            orders = []
            total_value = 0
            
            for symbol, allocation in portfolio_allocation.items():
                shares = allocation.get("position_size_shares", 0)
                price = allocation.get("estimated_price", 0)
                
                if shares > 0 and price > 0:
                    order_value = shares * price
                    orders.append({
                        "symbol": symbol,
                        "action": "buy",
                        "quantity": shares,
                        "estimated_price": price,
                        "estimated_value": order_value,
                        "order_type": "market",
                        "confidence": allocation.get("confidence", 0.8),
                        "target_price": allocation.get("target_price", 0),
                        "stop_loss": allocation.get("stop_loss", 0)
                    })
                    total_value += order_value
            
            # Create comprehensive execution plan
            execution_plan = {
                "status": "ready",
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "orders": orders,
                "total_orders": len(orders),
                "total_estimated_value": total_value,
                "cash_reserve": user_prefs.get("budget", 0) - total_value,
                "execution_mode": user_prefs.get("mode", "virtual"),
                "strategy": investment_plan.get("investment_plan", {}).get("strategy", "swing"),
                "risk_management": investment_plan.get("investment_plan", {}).get("risk_management", {}),
                "execution_timeline": "immediate",
                "monitoring_plan": {
                    "review_frequency": "daily",
                    "rebalance_schedule": "monthly",
                    "performance_tracking": True,
                    "alerts_enabled": True
                },
                "approved": len(orders) > 0
            }
            
            message = SystemMessage(
                content=f"📋 Execution Plan Ready\n"
                        f"Orders: {len(orders)}\n"
                        f"Total Value: ${total_value:,.2f}\n"
                        f"Mode: {execution_plan['execution_mode']}\n"
                        f"Status: {'✅ Approved' if execution_plan['approved'] else '❌ Needs Review'}"
            )
            
            return {
                "messages": [message],
                "execution_plan": execution_plan
            }
            
        except Exception as e:
            logging.error(f"Execution planning error: {str(e)}")
            error_message = SystemMessage(content=f"❌ Execution planning error: {str(e)}")
            return {"messages": [error_message], "execution_plan": {}}

    def _validation_node(self, state: State):
        """Validate the complete trading plan"""
        try:
            investment_plan = state.get("investment_plan", {})
            portfolio_allocation = state.get("portfolio_allocation", {})
            execution_plan = state.get("execution_plan", {})
            
            logging.info("Validating trading plan...")
            
            validation_results = {
                "validation_status": "passed",
                "checks_performed": [],
                "warnings": [],
                "errors": [],
                "recommendations": []
            }
            
            # Check 1: Budget allocation
            plan_data = investment_plan.get("investment_plan", {})
            total_budget = plan_data.get("total_budget", 0)
            allocated_value = execution_plan.get("total_estimated_value", 0)
            
            validation_results["checks_performed"].append("Budget allocation check")
            
            if allocated_value > total_budget * 0.95:  # More than 95% allocated
                validation_results["warnings"].append(f"High allocation: {allocated_value/total_budget*100:.1f}% of budget")
            
            # Check 2: Position sizes
            validation_results["checks_performed"].append("Position size check")
            for symbol, allocation in portfolio_allocation.items():
                position_pct = allocation.get("allocation_percentage", 0)
                if position_pct > 30:
                    validation_results["warnings"].append(f"{symbol}: Large position size ({position_pct:.1f}%)")
            
            # Check 3: Order validity
            validation_results["checks_performed"].append("Order validity check")
            orders = execution_plan.get("orders", [])
            if not orders:
                validation_results["errors"].append("No valid orders generated")
                validation_results["validation_status"] = "failed"
            
            # Add recommendations
            if len(orders) < 3:
                validation_results["recommendations"].append("Consider more diversification with additional positions")
            
            if execution_plan.get("cash_reserve", 0) < total_budget * 0.05:
                validation_results["recommendations"].append("Maintain at least 5% cash reserve")
            
            message = SystemMessage(
                content=f"✅ Validation Complete\n"
                        f"Status: {validation_results['validation_status'].upper()}\n"
                        f"Checks: {len(validation_results['checks_performed'])}\n"
                        f"Warnings: {len(validation_results['warnings'])}\n"
                        f"Errors: {len(validation_results['errors'])}"
            )
            
            return {
                "messages": [message],
                "validation_results": validation_results
            }
            
        except Exception as e:
            logging.error(f"Validation error: {str(e)}")
            error_message = SystemMessage(content=f"❌ Validation error: {str(e)}")
            return {"messages": [error_message], "validation_results": {"validation_status": "failed"}}

    def _final_output_node(self, state: State):
        """Generate final structured output and save to database"""
        try:
            # Use the existing action_executor_agent with enhanced data
            return self.agents.action_executor_agent(state)
            
        except Exception as e:
            logging.error(f"Final output error: {str(e)}")
            error_message = SystemMessage(content=f"❌ Final output error: {str(e)}")
            return {"messages": [error_message]}

    def _extract_json_from_response(self, response_content: str, expected_key: str = None):
        """Helper method to extract JSON from LLM response"""
        try:
            # Remove markdown code blocks
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            else:
                json_content = response_content.strip()
            
            # Parse JSON
            parsed_json = json.loads(json_content)
            return parsed_json
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error: {e}")
            # Return empty structure if expected_key provided
            if expected_key:
                return {expected_key: {}}
            return {}
        except Exception as e:
            logging.error(f"JSON extraction error: {e}")
            return {}
    




    
    #@tool(description="FireCrawl for advance crawling websites related to the economic terms Query")
    def _firecrawl_search(self, state: State):
        query = state.get("query", "financial market")
        
        try:
            # Get serialized results
            search_results = self.firecrawl.search_financial_services(query)
            
            # Create a system message with the search results
            result_message = SystemMessage(
                content=f"Firecrawl search results for query '{query}':\n{json.dumps(search_results, indent=2)}"
            )
            
            # Initialize firecrawl_data list
            firecrawl_data = []
            
            # Process search results if they exist
            if search_results and isinstance(search_results, dict) and search_results.get('data'):
                for result_item in search_results['data'][:5]:  # Limit to first 3 results
                    if isinstance(result_item, dict) and result_item.get('url'):
                        scraped_data = self.firecrawl.scrape_financial_website(url=result_item['url'])
                        if scraped_data:
                            firecrawl_data.append(scraped_data)
            
            # Get market data
            market_data = self.firecrawl.search_market_data(query=query)
            if market_data:
                firecrawl_data.append(market_data)
            
            # Get economic data
            economic_data = self.firecrawl.scrape_economic_data(indicator=query)
            if economic_data:
                firecrawl_data.append(economic_data)
            
            # Create consolidated message with all data
            consolidated_message = SystemMessage(
                content=f"Firecrawl crawling results for query '{query}':\n{json.dumps(firecrawl_data, indent=2)}"
            )
            #logging.info(f"Completed firecrawl search for query: {query}. \n answer: {consolidated_message} \n" )
            # Return updated state with new messages
            return {"messages": [result_message, consolidated_message]}
            
        except Exception as e:
            error_message = SystemMessage(
                content=f"Error during firecrawl search: {str(e)}"
            )
            return {"messages": [error_message]}
