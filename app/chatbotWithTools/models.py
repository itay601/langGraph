from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class FinancialAnalysis(BaseModel):
    """Structured output for LLM financial service analysis"""
    pricing_model: str  # Free, Freemium, Paid, Enterprise, Unknown
    is_data_provider: Optional[bool] = None  # Whether it provides financial data
    financial_metrics: List[str] = []  # P/E, ROI, Beta, etc.
    description: str = ""
    api_available: Optional[bool] = None
    market_coverage: List[str] = []  # NYSE, NASDAQ, LSE, etc.
    integration_platforms: List[str] = []  # TradingView, Bloomberg, etc.
    real_time_data: Optional[bool] = None  # Real-time vs delayed data


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
    extracted_tools: List[str] = []  # Financial tools extracted from articles
    companies: List[CompanyInfo] = []
    search_results: List[Dict[str, Any]] = []
    analysis: Optional[str] = None