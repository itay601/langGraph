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
    stock_ticker: str               
    company_name: str               
    industry: str                   
    geographic_focus: Optional[str] = None  
    
    # Economic and Market Analysis
    economic_context: Optional[str] = ""      
    current_stock_performance: Optional[str] = ""
    market_analysis: Optional[str] = ""         
    
    # Future Outlook and Risk Assessment
    future_outlook: Optional[str] = ""          
    risk_assessment: Optional[str] = ""         
    recommendation: Optional[str] = ""          
    
    # Financial & Valuation Metrics
    valuation_metrics: List[str] = []           
    financial_health_summary: Optional[str] = ""
    
    # Additional Details
    pricing_model: Optional[str] = None         
    api_available: Optional[bool] = None         
    integration_platforms: List[str] = []        
    real_time_data: Optional[bool] = None        
    additional_comments: Optional[str] = ""


class CompanyInfo(BaseModel):
    name: str
    description: str
    website: str
    pricing_model: Optional[str] = None
    is_data_provider: Optional[bool] = None
    financial_metrics: List[str] = []
    competitors: List[str] = []
    

    api_available: Optional[bool] = None
    market_coverage: List[str] = []  
    integration_platforms: List[str] = []  
    real_time_data: Optional[bool] = None 
    analysis_tools: List[str] = []  
    asset_classes: List[str] = []  


class ResearchState(BaseModel):
    query: str
    extracted_tools: List[str] = []  
    companies: Optional[CompanyInfo] = None
    search_results: List[Dict[str, Any]] = []
    analysis: Optional[CompanyFinancialReviewAnalysis] = None
    
    # Additional workflow state
    router_decision: Optional[str] = None 
    crawl_results: List[Dict[str, Any]] = []
    db_articles: List[Dict[str, Any]] = []  
    processing_status: str = "initialized"  
    created_at: datetime = datetime.now()


class FinancialArticle(BaseModel):
    """Model for financial articles from DB or web crawling"""
    title: str
    content: str
    source: str
    url: Optional[str] = None
    published_date: Optional[datetime] = None
    relevance_score: Optional[float] = None
    article_type: str = "financial"  


class RouterDecision(BaseModel):
    """Model for router decisions"""
    decision_type: str  
    confidence: float   
    reasoning: str
    extracted_entities: List[str] = []  
    suggested_tools: List[str] = []     


class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    processing_time: Optional[float] = None