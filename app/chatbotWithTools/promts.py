class FinancialToolsPrompts:
    """Collection of prompts for analyzing financial tools and services"""

    # Financial tool extraction prompts
    TOOL_EXTRACTION_SYSTEM = """You are a financial analyst and researcher. Extract specific financial tool, platform, service, or data provider names from articles.
                            Focus on actual products/services that investors, traders, or financial analysts can use, not general concepts or market terminology."""

    @staticmethod
    def tool_extraction_user(query: str, content: str) -> str:
        return f"""Query: {query}
                Article Content: {content}

                Extract a list of specific financial tool/service names mentioned in this content that are relevant to "{query}".

                Rules:
                - Only include actual product names, not generic financial terms
                - Focus on tools investors/traders can directly use
                - Include both free and paid financial services
                - Include data providers, trading platforms, analysis tools
                - Limit to the 5 most relevant tools
                - Return just the tool names, one per line, no descriptions

                Example format:
                Yahoo Finance
                Bloomberg Terminal
                TradingView
                Alpha Vantage
                Quandl"""

    # Financial service analysis prompts
    TOOL_ANALYSIS_SYSTEM = """You are analyzing financial tools, trading platforms, and market data services. 
                            Focus on extracting information relevant to investors, traders, and financial analysts. 
                            Pay special attention to market data, trading capabilities, financial metrics, and analysis features."""

    @staticmethod
    def tool_analysis_user(company_name: str, content: str) -> str:
        return f"""Financial Service: {company_name}
                Website Content: {content[:2500]}

                Analyze this content from a financial/investment perspective and provide:
                - pricing_model: One of "Free", "Freemium", "Paid", "Enterprise", or "Unknown"
                - is_data_provider: true if provides financial/market data, false if not, null if unclear
                - financial_metrics: List of financial metrics supported (P/E ratio, RSI, MACD, Beta, ROI, etc.)
                - description: Brief 1-sentence description focusing on what this service does for investors/traders
                - api_available: true if REST API, WebSocket, or programmatic access for financial data is mentioned
                - market_coverage: List of markets/exchanges covered (NYSE, NASDAQ, LSE, crypto exchanges, forex, etc.)
                - integration_platforms: List of platforms it integrates with (TradingView, MetaTrader, Excel, etc.)
                - real_time_data: true if real-time market data, false if delayed, null if unclear

                Focus on investment-relevant features like market data, trading capabilities, portfolio management, and financial analysis tools."""

    # Investment reviuer prompts
    RECOMMENDATIONS_SYSTEM = """You are a senior financial analyst providing quick, actionable investment tool recommendationer by risks and apartunities. 
                            Keep responses brief and practical - maximum 4-5 sentences total."""

    @staticmethod
    def recommendations_user(query: str, company_data: str) -> str:
        return f"""Financial Query: {query}
                Financial Tools/Services Analyzed: {company_data}

                Provide a brief recommendation (3-4 sentences max) covering:
                - Which tool/service is best for the query and why
                - Key cost/pricing consideration for investors
                - Main advantage for financial analysis or trading

                Be concise and direct - focus on practical investment value."""