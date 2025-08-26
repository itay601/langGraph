"""
Trading Bot Prompt Templates for Structured Output
This module contains carefully crafted prompts to ensure LLM generates
the exact JSON structure needed for the trading bot.
"""

def create_investment_analysis_prompt(user_prefs: dict) -> str:
    """
    Creates a structured prompt that forces the LLM to use tools and generate JSON
    """
    query = user_prefs.get("query", "")
    budget = user_prefs.get("budget", 0)
    strategy = user_prefs.get("strategy", "swing")
    risk = user_prefs.get("risk", "medium")
    preferred_markets = user_prefs.get("preferred_markets", ["stocks"])
    
    prompt = f"""
You are a professional trading analyst AI. You MUST follow these steps exactly and use the available tools.

STEP 1 - MARKET RESEARCH (MANDATORY):
1. Use get_reddit_vibe("{query}") to analyze current market sentiment
2. Use get_stock_data_yahoo for at least 3 stocks to get historical data
3. Use get_ticker_data_poly to get recent price data for selected stocks

STEP 2 - ANALYSIS:
Based on the tool results, analyze:
- Market sentiment from Reddit data
- Historical performance patterns
- Current price trends
- Risk factors for {risk} risk tolerance
- Alignment with {strategy} strategy

STEP 3 - STOCK SELECTION:
Select 5-8 stocks that match:
- User interest: {query}
- Risk level: {risk}
- Strategy: {strategy}
- Markets: {preferred_markets}
- Budget: ${budget}

STEP 4 - GENERATE EXACT JSON OUTPUT:
You MUST respond with ONLY the following JSON structure. NO other text before or after:

{{
    "trading_plan": {{
        "status": "generated",
        "timestamp": "2024-01-XX 10:XX:XX",
        "strategy": "{strategy}",
        "risk_level": "{risk}",
        "total_budget": {budget},
        "user_query": "{query}",
        "market_analysis": {{
            "sentiment_score": 0.0,
            "sentiment_summary": "Based on Reddit analysis...",
            "key_trends": ["trend1", "trend2", "trend3"],
            "risk_factors": ["factor1", "factor2"],
            "market_outlook": "positive/negative/neutral"
        }},
        "selected_stocks": [
            {{
                "symbol": "STOCK1",
                "company_name": "Company Name 1",
                "current_price": 0.00,
                "allocation_percentage": 25.0,
                "allocation_amount": 12500.0,
                "shares_to_buy": 125,
                "target_price": 0.00,
                "stop_loss_price": 0.00,
                "confidence_score": 8.5,
                "reasoning": "Detailed reason why this stock fits {strategy} strategy and {risk} risk level",
                "expected_return": 15.0,
                "time_horizon": "3-6 months"
            }},
            {{
                "symbol": "STOCK2",
                "company_name": "Company Name 2",
                "current_price": 0.00,
                "allocation_percentage": 20.0,
                "allocation_amount": 10000.0,
                "shares_to_buy": 100,
                "target_price": 0.00,
                "stop_loss_price": 0.00,
                "confidence_score": 7.8,
                "reasoning": "Detailed reason why this stock fits the criteria",
                "expected_return": 12.0,
                "time_horizon": "2-4 months"
            }}
        ],
        "risk_management": {{
            "max_single_position": 25.0,
            "cash_reserve_percentage": 10.0,
            "stop_loss_percentage": 8.0,
            "take_profit_percentage": 20.0,
            "position_sizing_method": "equal_weight",
            "rebalance_frequency": "monthly"
        }},
        "execution_plan": {{
            "execution_timeline": "immediate",
            "order_type": "market",
            "execution_mode": "{user_prefs.get('mode', 'virtual')}",
            "monitoring_frequency": "daily",
            "review_date": "2024-02-XX"
        }},
        "performance_targets": {{
            "expected_annual_return": 12.0,
            "maximum_drawdown": 15.0,
            "sharpe_ratio_target": 1.2,
            "success_metrics": ["total_return", "risk_adjusted_return", "drawdown_control"]
        }},
        "next_actions": [
            "Execute buy orders for selected stocks",
            "Set up stop-loss and take-profit orders",
            "Monitor daily price movements",
            "Review portfolio allocation monthly",
            "Adjust positions based on market conditions"
        ]
    }}
}}

CRITICAL REQUIREMENTS:
1. Use actual data from tool calls - replace 0.00 with real prices
2. Ensure allocation percentages sum to ≤ 90% (keep 10% cash)
3. Calculate exact shares_to_buy based on allocation_amount ÷ current_price
4. Set target_price 15-25% above current_price
5. Set stop_loss_price 8-12% below current_price
6. Provide specific reasoning for each stock selection
7. Replace placeholder dates with actual dates
8. Base sentiment_score on actual Reddit data (-1 to +1 scale)

DO NOT include any text before or after the JSON. Start directly with {{ and end with }}.
"""
    return prompt

def create_portfolio_optimization_prompt(investment_plan: dict) -> str:
    """
    Creates a prompt for optimizing portfolio allocation
    """
    return f"""
You are a portfolio optimization specialist. Analyze the investment plan and optimize allocations.

CURRENT PLAN:
{investment_plan}

TASK: Optimize the portfolio allocation considering:
1. Risk diversification
2. Correlation between selected stocks
3. Sector balance
4. Volatility management

Generate optimized JSON with improved allocations while maintaining the same structure.
Return ONLY the optimized JSON, no other text.
"""

def create_execution_planning_prompt(portfolio_data: dict) -> str:
    """
    Creates a prompt for detailed execution planning
    """
    return f"""
You are an execution planning specialist. Create a detailed execution plan.

PORTFOLIO DATA:
{portfolio_data}

Generate a comprehensive execution plan JSON with:
- Order sequencing
- Timing strategy
- Risk controls
- Monitoring checkpoints

Return ONLY JSON format matching the trading_plan structure.
"""

def create_market_analysis_prompt(query: str) -> str:
    """
    Creates a focused prompt for market analysis using tools
    """
    return f"""
You are a market research analyst. Perform comprehensive market analysis for: {query}

MANDATORY STEPS:
1. Use get_reddit_vibe("{query}") for sentiment analysis
2. Use get_related_articles("{query}") for news analysis
3. Use stock data tools for price analysis

Generate market analysis JSON:
{{
    "market_analysis": {{
        "sentiment_score": 0.0,
        "sentiment_summary": "...",
        "news_summary": "...",
        "price_trends": "...",
        "key_insights": ["...", "..."],
        "risk_factors": ["...", "..."],
        "opportunities": ["...", "..."]
    }}
}}

Use tools FIRST, then analyze results. Return ONLY JSON.
"""

# Validation prompts to ensure data quality
def create_validation_prompt(trading_plan: dict) -> str:
    """
    Creates a prompt to validate and fix trading plan issues
    """
    return f"""
You are a trading plan validator. Review this plan and fix any issues:

PLAN TO VALIDATE:
{trading_plan}

CHECK AND FIX:
1. Allocation percentages sum to ≤ 90%
2. All prices are realistic (> 0)
3. Shares calculations are correct
4. Stop-loss and targets are reasonable
5. All required fields are present

Return the corrected plan in the same JSON structure. ONLY JSON, no other text.
"""

# Example usage functions
def get_sample_prompts():
    """
    Returns sample prompts for testing
    """
    sample_user_prefs = {
        "query": "AI and technology growth stocks",
        "budget": 50000,
        "strategy": "swing",
        "risk": "medium",
        "preferred_markets": ["stocks"],
        "mode": "virtual"
    }
    
    return {
        "investment_analysis": create_investment_analysis_prompt(sample_user_prefs),
        "market_analysis": create_market_analysis_prompt("AI technology stocks"),
        "validation": "Use create_validation_prompt() with actual trading plan data"
    }

# System prompts for different agents
SYSTEM_PROMPTS = {
    "analyst": """You are a professional stock market analyst with expertise in technical and fundamental analysis. 
    You MUST use available tools to gather real market data before making recommendations. 
    Always provide data-driven insights and specific reasoning for stock selections.""",
    
    "portfolio_manager": """You are a portfolio management specialist focused on risk-adjusted returns. 
    Your job is to optimize allocations, manage risk, and create balanced portfolios. 
    Consider correlation, diversification, and risk management in all decisions.""",
    
    "execution_specialist": """You are a trade execution specialist responsible for implementing investment plans. 
    Focus on optimal timing, order management, and risk controls. 
    Ensure all executions align with the overall strategy and risk parameters."""