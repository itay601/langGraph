from pydantic import BaseModel
from typing import List, Literal, Optional

class UserPreferences(BaseModel):
    query: str
    budget: float
    stocks: List[str]
    risk: Literal['low', 'medium', 'high']
    mode: Literal['virtual', 'live']
    strategy: Literal['day_trading', 'swing', 'long_term', 'scalping'] = None
    stop_loss: Optional[float] = Field(None, ge=0, le=100, description="Stop loss percentage per trade")
    take_profit: Optional[float] = Field(None, ge=0, le=100, description="Take profit percentage per trade")
    max_drawdown: Optional[float] = Field(None, ge=0, le=100, description="Maximum acceptable portfolio drawdown")
    leverage: Optional[float] = Field(1.0, ge=1.0, description="Trading leverage multiplier")
    trade_frequency: Optional[Literal['low', 'medium', 'high']] = None
    notifications: Optional[Literal['email', 'sms', 'push', 'none']] = "none"
    preferred_markets: Optional[List[Literal['stocks', 'crypto', 'forex', 'etf']]] = ["stocks"]