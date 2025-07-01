from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class CompanyFinancialReviewAnalysis(BaseModel):
    """
    Structured output for LLM financial review analysis.
    This data structure is designed to analyze a company's stock performance,
    economic context, and future prospects, providing users with an in-depth view.
    """
    # Identification and Contextual Information
    stock_ticker: str               # e.g., "AAPL", "GOOGL"
    company_name: str               # Full name of the company
    industry: str                   # The sector or industry (e.g., Technology, Healthcare)
    geographic_focus: Optional[str] = None  # e.g., Global, US, European markets
    
    # Economic and Market Analysis
    economic_context: Optional[str] = ""      # Overview of the current economic climate affecting the company
    current_stock_performance: Optional[str] = ""  # Analysis of recent stock movements and performance
    market_analysis: Optional[str] = ""         # Broader market performance and competitor comparison
    
    # Future Outlook and Risk Assessment
    future_outlook: Optional[str] = ""          # Forward-looking assessment of the company's prospects
    risk_assessment: Optional[str] = ""         # Factors that might affect future performance (e.g., market volatility, regulatory risks)
    recommendation: Optional[str] = ""          # Investment recommendation (e.g., Buy, Hold, Sell)
    
    # Financial & Valuation Metrics
    valuation_metrics: List[str] = []           # List metrics such as P/E, ROI, Beta, etc.
    financial_health_summary: Optional[str] = ""# Summarized view on liquidity, debt, and overall financial health
    
    # Additional Details
    pricing_model: Optional[str] = None         # Pricing model for related services, if applicable (Free, Freemium, Paid, Enterprise, Unknown)
    api_available: Optional[bool] = None          # Whether related API services are available
    integration_platforms: List[str] = []         # e.g., TradingView, Bloomberg, etc.
    real_time_data: Optional[bool] = None         # Indicates availability of real-time data vs delayed
    additional_comments: Optional[str] = ""       # Any further insights or detailed comments


class CompanyInfo(BaseModel):
    name: str
    description: str
    website: str
    pricing_model: Optional[str] = None
    is_data_provider: Optional[bool] = None  # Financial data provider
    financial_metrics: List[str] = []  # Financial metrics supported
    competitors: List[str] = []
    
    # Finance-specific fields
    api_available: Optional[bool] = None
    market_coverage: List[str] = []  # Markets covered (NYSE, NASDAQ, etc.)
    integration_platforms: List[str] = []  # Integration with trading platforms
    real_time_data: Optional[bool] = None  # Real-time data availability
    analysis_tools: List[str] = []  # Technical analysis, fundamental analysis, etc.
    asset_classes: List[str] = []  # Stocks, bonds, crypto, forex, etc.


class ResearchState(BaseModel):
    query: str
    extracted_tools: List[str] = []  # Financial tools -- extracted articles from DB. crawling websites related
    companies: Optional[CompanyInfo] = None
    search_results: List[Dict[str, Any]] = []
    analysis: Optional[CompanyFinancialReviewAnalysis] = None
    
    # Additional workflow state
    router_decision: Optional[str] = None  # What type of analysis was requested
    crawl_results: List[Dict[str, Any]] = []  # Results from web crawling
    db_articles: List[Dict[str, Any]] = []   # Articles from database/vector search
    processing_status: str = "initialized"   # Status tracking
    created_at: datetime = datetime.now()


class FinancialArticle(BaseModel):
    """Model for financial articles from DB or web crawling"""
    title: str
    content: str
    source: str
    url: Optional[str] = None
    published_date: Optional[datetime] = None
    relevance_score: Optional[float] = None
    article_type: str = "financial"  # news, analysis, report, etc.


class RouterDecision(BaseModel):
    """Model for router decisions"""
    decision_type: str  # "company_analysis", "market_analysis", "general_financial"
    confidence: float   # 0.0 to 1.0
    reasoning: str
    extracted_entities: List[str] = []  # Company names, stock tickers, etc.
    suggested_tools: List[str] = []     # Which tools to use


class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    processing_time: Optional[float] = None