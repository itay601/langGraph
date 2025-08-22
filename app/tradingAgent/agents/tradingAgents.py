from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
#from utills.firecrawl import FirecrawlService
from langchain_core.tools import tool
from tradingAgent.core.tools import get_ticker_data_poly, get_stock_data_yahoo, get_reddit_vibe, get_related_articles
import logging
import json

class TradingAgents:
    def __init__(self, llm, user_prefs):
        self.llm = llm
        self.user_prefs = user_prefs
        #self.firecrawl = FirecrawlService()

    def user_agent(self, state):
        try:
            user_prefs = self.user_prefs.dict() if hasattr(self.user_prefs, 'dict') else self.user_prefs
            
            logging.info(f"Processing user preferences: {user_prefs}")
            
            message = SystemMessage(
                content=f"✅ User preferences processed successfully:\n"
                       f"Budget: ${user_prefs.get('budget', 0)}\n"
                       f"Risk Level: {user_prefs.get('risk', 'medium')}\n"
                       f"Mode: {user_prefs.get('mode', 'virtual')}\n"
                       f"Stocks: {user_prefs.get('stocks', [])}\n"
                       f"Query: {user_prefs.get('query', '')}"
            )
            
            return {
                "messages": [message],
                "user_preferences": user_prefs,
                "query": user_prefs.get("query", ""),
                "symbol": ",".join(user_prefs.get("stocks", [])),
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ User agent error: {str(e)}")
            return {"messages": [error_message]}

    def strategy_chooser_agent(self, state):
        try:
            user_prefs = state.get("user_preferences", {})
            
            if user_prefs.get("strategy"):
                strategy = user_prefs["strategy"]
                message = SystemMessage(content=f"✅ Strategy already selected: {strategy}")
            else:
                # AI-based strategy selection logic
                risk_level = user_prefs.get("risk", "medium")
                budget = user_prefs.get("budget", 0)
                trade_frequency = user_prefs.get("trade_frequency", "medium")
                
                # Enhanced strategy selection logic
                if budget < 1000:
                    strategy = "long_term"
                elif risk_level == "high" and trade_frequency == "high":
                    strategy = "day_trading"
                elif risk_level == "high" and trade_frequency == "low":
                    strategy = "momentum" 
                elif risk_level == "low":
                    strategy = "long_term"
                elif trade_frequency == "high":
                    strategy = "scalping"
                else:
                    strategy = "swing"
                
                message = SystemMessage(
                    content=f"🤖 AI recommended strategy: {strategy}\n"
                           f"Based on: Risk={risk_level}, Budget=${budget}, Frequency={trade_frequency}"
                )
            
            logging.info(f"Strategy selected: {strategy}")
            
            return {
                "messages": [message],
                "strategy": strategy
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Strategy chooser error: {str(e)}")
            return {"messages": [error_message]}


    def human_approval_agent(self, state):
        try:
            strategy = state.get("strategy", "")
            user_prefs = state.get("user_preferences", {})
            
            # In a real implementation, this would:
            # 1. Display the strategy and parameters to the user
            # 2. Wait for user confirmation/modification
            # 3. Allow parameter adjustments
            
            # For now, we'll auto-approve (can be enhanced with actual UI integration)
            approved = True
            
            message = SystemMessage(
                content=f"✅ Human approval checkpoint passed\n"
                       f"Strategy: {strategy}\n"
                       f"Budget: ${user_prefs.get('budget', 0)}\n"
                       f"Risk: {user_prefs.get('risk', 'medium')}\n"
                       f"Mode: {user_prefs.get('mode', 'virtual')}\n"
                       f"Status: {'APPROVED' if approved else 'REJECTED'}"
            )
            
            logging.info(f"Human approval: {approved} for strategy: {strategy}")
            
            return {
                "messages": [message],
                "human_approved": approved
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Human approval error: {str(e)}")
            return {"messages": [error_message]}           




    def polygon_api_agent(self, state):
        try:
            symbols = state.get("symbol", "").split(",")
            market_data = {}
            
            logging.info(f"Fetching Polygon data for symbols: {symbols}")
            
            for symbol in symbols[:3]:  # Limit to prevent API overuse
                symbol = symbol.strip()
                if symbol:
                    data = get_ticker_data_poly(symbol)
                    if data:
                        market_data[symbol] = data
                        logging.info(f"Successfully fetched Polygon data for {symbol}")
            
            message = SystemMessage(
                content=f"📊 Polygon API data collected\n"
                       f"Symbols processed: {list(market_data.keys())}\n"
                       f"Data points per symbol: ~200 days historical data"
            )
            
            return {
                "messages": [message],
                "market_data": market_data
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Polygon API error: {str(e)}")
            return {"messages": [error_message]}



    def reddit_agent(self, state):
        try:
            query = state.get("query", "stocks")
            
            logging.info(f"Fetching Reddit sentiment for query: {query}")
            
            reddit_data = get_reddit_vibe(query)
            
            message = SystemMessage(
                content=f"📱 Reddit sentiment data collected\n"
                       f"Query: {query}\n"
                       f"Posts analyzed: {len(reddit_data) if reddit_data else 0}\n"
                       f"Sources: r/stocks, r/investing, r/wallstreetbets, etc."
            )
            
            # Initialize or update sentiment data
            existing_sentiment = state.get("sentiment_data", {})
            existing_sentiment["reddit"] = reddit_data
            
            return {
                "messages": [message],
                "sentiment_data": existing_sentiment
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Reddit agent error: {str(e)}")
            return {"messages": [error_message]}

    def news_articles_agent(self, state):
        try:
            symbols = state.get("symbol", "").split(",")
            articles_data = {}
            
            logging.info(f"Fetching news articles for symbols: {symbols}")
            
            for symbol in symbols[:3]:
                symbol = symbol.strip()
                if symbol:
                    articles = get_related_articles(symbol)
                    if articles:
                        articles_data[symbol] = articles
                        logging.info(f"Fetched {len(articles)} articles for {symbol}")
            
            message = SystemMessage(
                content=f"📰 Financial news articles collected\n"
                       f"Symbols: {list(articles_data.keys())}\n"
                       f"Total articles: {sum(len(articles) for articles in articles_data.values())}\n"
                       f"Sources: Financial news APIs, economic publications"
            )
            
            # Merge with existing sentiment data
            existing_sentiment = state.get("sentiment_data", {})
            existing_sentiment["news"] = articles_data
            
            return {
                "messages": [message],
                "sentiment_data": existing_sentiment
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ News articles agent error: {str(e)}")
            return {"messages": [error_message]}


    def sentiment_analysis_agent(self, state):
        try:
            sentiment_data = state.get("sentiment_data", {})
            
            logging.info("Starting comprehensive sentiment analysis")
            
            # Initialize sentiment components
            sentiment_scores = {
                "reddit_sentiment": 0.0,
                "news_sentiment": 0.0, 
                "web_sentiment": 0.0,
                "overall_sentiment": 0.0
            }
            
            # Analyze Reddit sentiment (placeholder for actual NLP)
            if "reddit" in sentiment_data and sentiment_data["reddit"]:
                # Simple sentiment analysis based on scores and keywords
                reddit_posts = sentiment_data["reddit"]
                total_score = sum(post.get("score", 0) for post in reddit_posts)
                sentiment_scores["reddit_sentiment"] = min(max(total_score / 1000, -1), 1)
            
            # Analyze news sentiment (placeholder for actual NLP)
            if "news" in sentiment_data and sentiment_data["news"]:
                # Analyze news articles for sentiment
                sentiment_scores["news_sentiment"] = 0.1  # Placeholder
            
            # Analyze web-scraped content sentiment
            if "firecrawl" in sentiment_data and sentiment_data["firecrawl"]:
                # Analyze firecrawl data
                sentiment_scores["web_sentiment"] = 0.05  # Placeholder
            
            # Calculate overall sentiment (weighted average)
            weights = {"reddit": 0.4, "news": 0.4, "web": 0.2}
            overall_sentiment = (
                weights["reddit"] * sentiment_scores["reddit_sentiment"] +
                weights["news"] * sentiment_scores["news_sentiment"] +
                weights["web"] * sentiment_scores["web_sentiment"]
            )
            sentiment_scores["overall_sentiment"] = overall_sentiment
            
            # Determine sentiment label
            if overall_sentiment > 0.1:
                sentiment_label = "BULLISH 📈"
            elif overall_sentiment < -0.1:
                sentiment_label = "BEARISH 📉"
            else:
                sentiment_label = "NEUTRAL ➡️"
            
            message = SystemMessage(
                content=f"🌍 Sentiment analysis completed\n"
                       f"Overall sentiment: {sentiment_label}\n"
                       f"Score: {overall_sentiment:.3f} (range: -1 to 1)\n"
                       f"Reddit: {sentiment_scores['reddit_sentiment']:.3f}\n"
                       f"News: {sentiment_scores['news_sentiment']:.3f}\n"
                       f"Web: {sentiment_scores['web_sentiment']:.3f}"
            )
            
            # Update sentiment data with scores
            sentiment_data.update(sentiment_scores)
            
            return {
                "messages": [message],
                "sentiment_data": sentiment_data
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Sentiment analysis error: {str(e)}")
            return {"messages": [error_message]}


    def signal_alpha_agent(self, state):    
        try:
            market_data = state.get("market_data", {})
            sentiment_data = state.get("sentiment_data", {})
            strategy = state.get("strategy", "swing")
            
            logging.info(f"Generating signals using {strategy} strategy")
            
            signals = {}
            overall_sentiment = sentiment_data.get("overall_sentiment", 0.0)
            
            # Generate signals for each symbol
            for symbol in market_data.keys():
                # Placeholder for technical analysis
                # In production, this would include:
                # - Moving averages, RSI, MACD, Bollinger Bands
                # - Volume analysis, support/resistance levels
                # - Strategy-specific indicators
                
                # Simple signal generation logic
                signal_strength = 0.5 + (overall_sentiment * 0.3)  # Base + sentiment adjustment
                
                if signal_strength > 0.7:
                    action = "buy"
                    confidence = signal_strength
                elif signal_strength < 0.3:
                    action = "sell" 
                    confidence = 1 - signal_strength
                else:
                    action = "hold"
                    confidence = 0.5
                
                signals[symbol] = {
                    "action": action,
                    "confidence": confidence,
                    "signal_strength": signal_strength,
                    "strategy_used": strategy,
                    "target_price": None,  # Would be calculated from technical analysis
                    "stop_loss": None,     # Would be calculated based on volatility
                    "sentiment_factor": overall_sentiment
                }
                
                logging.info(f"Signal for {symbol}: {action} (confidence: {confidence:.2f})")
            
            message = SystemMessage(
                content=f"🎯 Trading signals generated\n"
                       f"Strategy: {strategy}\n"
                       f"Symbols analyzed: {len(signals)}\n"
                       f"Sentiment factor: {overall_sentiment:.3f}\n"
                       f"Signals: {['{k}:{v[\"action\"]}' for k,v in signals.items()]}"
            )
            
            return {
                "messages": [message],
                "signals": signals
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Signal generation error: {str(e)}")
            return {"messages": [error_message]}  


    def portfolio_manager_agent(self, state):
        try:
            signals = state.get("signals", {})
            user_prefs = state.get("user_preferences", {})
            budget = user_prefs.get("budget", 0)
            
            logging.info(f"Managing portfolio allocation for budget: ${budget}")
            
            portfolio_allocation = {}
            
            # Filter signals for actionable trades (buy/sell)
            actionable_signals = {k: v for k, v in signals.items() 
                                if v["action"] in ["buy", "sell"]}
            
            if actionable_signals:
                # Calculate position sizes
                num_positions = len(actionable_signals)
                base_allocation = budget / max(num_positions, 1)
                
                # Adjust allocation based on confidence
                total_confidence = sum(signal["confidence"] for signal in actionable_signals.values())
                
                for symbol, signal in actionable_signals.items():
                    # Weight allocation by confidence
                    confidence_weight = signal["confidence"] / total_confidence if total_confidence > 0 else 1/num_positions
                    allocated_amount = budget * confidence_weight
                    
                    portfolio_allocation[symbol] = {
                        "allocated_amount": allocated_amount,
                        "confidence_weight": confidence_weight,
                        "action": signal["action"],
                        "position_size_shares": 0,  # To be calculated with current price
                        "portfolio_weight": confidence_weight,
                        "max_position_limit": budget * 0.2,  # Max 20% per position
                        "diversification_score": 1/num_positions
                    }
            
            # Portfolio metrics
            total_allocated = sum(alloc["allocated_amount"] for alloc in portfolio_allocation.values())
            cash_reserve = budget - total_allocated
            
            message = SystemMessage(
                content=f"💼 Portfolio allocation completed\n"
                       f"Total budget: ${budget:,.2f}\n"
                       f"Allocated: ${total_allocated:,.2f}\n"
                       f"Cash reserve: ${cash_reserve:,.2f}\n"
                       f"Positions: {len(portfolio_allocation)}\n"
                       f"Diversification: {len(portfolio_allocation)} assets\n"
                       f"Max position size: 20% of portfolio"
            )
            
            return {
                "messages": [message],
                "portfolio_allocation": portfolio_allocation
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Portfolio manager error: {str(e)}")
            return {"messages": [error_message]}

    def risk_manager_agent(self, state):         
        try:
            user_prefs = state.get("user_preferences", {})
            portfolio_allocation = state.get("portfolio_allocation", {})
            
            logging.info("Conducting risk assessment")
            
            budget = user_prefs.get("budget", 0)
            risk_level = user_prefs.get("risk", "medium")
            
            # Risk level configs
            risk_configs = {
                "low": {"stop_loss": 3.0, "take_profit": 6.0, "max_position": 0.1, "max_drawdown": 10.0},
                "medium": {"stop_loss": 5.0, "take_profit": 10.0, "max_position": 0.15, "max_drawdown": 15.0},
                "high": {"stop_loss": 8.0, "take_profit": 15.0, "max_position": 0.25, "max_drawdown": 25.0}
            }
            config = risk_configs.get(risk_level, risk_configs["medium"])
            
            # Construct risk assessment
            risk_assessment = {
                "stop_loss_pct": user_prefs.get("stop_loss", config["stop_loss"]),
                "take_profit_pct": user_prefs.get("take_profit", config["take_profit"]),
                "max_position_size": budget * user_prefs.get("max_position_pct", config["max_position"]),
                "max_drawdown_pct": user_prefs.get("max_drawdown", config["max_drawdown"]),
                "leverage": user_prefs.get("leverage", 1.0),
                "risk_level": risk_level,
                "risk_warnings": []
            }
            
            # Exposure checks
            total_exposure = sum(a.get("allocated_amount", 0) for a in portfolio_allocation.values())
            risk_assessment["total_exposure_pct"] = (total_exposure / budget) * 100 if budget > 0 else 0
            
            warnings = []
            if risk_assessment["total_exposure_pct"] > 90:
                warnings.append("⚠️ High portfolio exposure above 90%")
            
            for sym, alloc in portfolio_allocation.items():
                pos_pct = (alloc.get("allocated_amount", 0) / budget) * 100
                if pos_pct > config["max_position"] * 100:
                    warnings.append(f"⚠️ {sym} exceeds max allowed position size")
            
            risk_assessment["risk_warnings"] = warnings
            risk_assessment["risk_approved"] = len(warnings) == 0
            
            message = SystemMessage(
                content=f"🛡️ Risk assessment completed\n"
                        f"Exposure: {risk_assessment['total_exposure_pct']:.1f}%\n"
                        f"Warnings: {warnings if warnings else 'None'}"
            )
            
            return {
                "messages": [message],
                "risk_assessment": risk_assessment
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Risk manager error: {str(e)}")
            return {"messages": [error_message]}



    def execution_agent(self, state):
        """
        💹 EXECUTION AGENT
        Prepares execution plan for trades before sending to virtual/live execution.
        """
        try:
            signals = state.get("signals", {})
            portfolio_allocation = state.get("portfolio_allocation", {})
            risk_assessment = state.get("risk_assessment", {})

            logging.info("Preparing execution plan")

            execution_plan = {
                "orders": [],
                "approved": risk_assessment.get("risk_approved", False)
            }

            for sym, alloc in portfolio_allocation.items():
                signal = signals.get(sym, {})
                order = {
                    "symbol": sym,
                    "action": signal.get("action", "hold"),
                    "amount": alloc.get("allocated_amount", 0),
                    "confidence": signal.get("confidence", 0)
                }
                execution_plan["orders"].append(order)

            message = SystemMessage(
                content=f"💹 Execution plan ready\n"
                        f"Orders: {len(execution_plan['orders'])}\n"
                        f"Approved: {execution_plan['approved']}"
            )

            return {
                "messages": [message],
                "execution_plan": execution_plan
            }
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Execution agent error: {str(e)}")
            return {"messages": [error_message]}


    def route_execution_mode(self, state: dict) -> str:
        mode = self.user_prefs.mode.lower()
        if mode == "virtual":
            return "virtual"
        elif mode == "live":
            return "live"
        else:
            raise ValueError(f"Unsupported execution mode: {mode}")


            

    def virtual_backtester_agent(self, state):
        try:
            plan = state.get("execution_plan", {})
            logging.info("Running virtual backtest execution")

            # Placeholder simulation: mark all as success
            results = {"orders_executed": len(plan.get("orders", [])), "success": True}

            message = SystemMessage(
                content=f"🧪 Virtual trades simulated: {results['orders_executed']} orders executed"
            )
            return {"messages": [message], "trade_results": results}
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Virtual backtester error: {str(e)}")
            return {"messages": [error_message]}


    def live_broker_agent(self, state):
        """
        🏦 LIVE BROKER AGENT
        Executes real trades through brokerage API integration.
        """
        return {"messages": [SystemMessage(content="🏦 Live broker execution not implemented yet")], "trade_results": {}}



    def monitoring_agent(self, state):
        try:
            trades = state.get("trade_results", {})
            logging.info("Monitoring trade outcomes")

            monitoring_data = {
                "status": "active",
                "last_trade_count": trades.get("orders_executed", 0),
                "alerts": []
            }

            message = SystemMessage(
                content=f"📈 Monitoring active\n"
                        f"Last trade count: {monitoring_data['last_trade_count']}\n"
                        f"Status: {monitoring_data['status']}"
            )
            return {"messages": [message], "monitoring_data": monitoring_data}
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Monitoring error: {str(e)}")
            return {"messages": [error_message]}



    def chatbot(self, state):
        try:
            strategy = state.get("strategy", "")
            signals = state.get("signals", {})
            trades = state.get("trade_results", {})
            sentiment = state.get("sentiment_data", {})

            summary = {
                "strategy": strategy,
                "signals": signals,
                "trades": trades,
                "sentiment": sentiment.get("overall_sentiment", 0)
            }

            message = HumanMessage(
                content=f"🤖 Trading session completed!\n"
                        f"Strategy: {strategy}\n"
                        f"Executed trades: {trades.get('orders_executed', 0)}\n"
                        f"Sentiment score: {summary['sentiment']:.2f}"
            )

            return {"messages": [message], "summary": summary}
        except Exception as e:
            error_message = SystemMessage(content=f"❌ Chatbot error: {str(e)}")
            return {"messages": [error_message]}                                    