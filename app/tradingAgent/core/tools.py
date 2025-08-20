import requests
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv 
import yfinance as yf
from langchain_core.tools import tool 


@tool(description="fetch stock data 200 days history using polygone.")
def get_ticker_data(ticker):
    load_dotenv()
    POLYGON_API_KEY= os.environ["POLYGON_API_KEY"]
    # Get date range for the last 200 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=200)
    
    # Function to format date as YYYY-MM-DD
    def format_date(date):
        return date.strftime('%Y-%m-%d')
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{format_date(start_date)}/{format_date(end_date)}?sort=asc&limit=200&apiKey={POLYGON_API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  
        data = response.json()
        return data
    except requests.exceptions.RequestException as error:
        print(f'Error fetching ticker data: {error}')
        return None



# List of stock tickers (deduplicated)
stocks = list([
    "AAPL", "TSLA", "AMZN", "MSFT", "NVDA", "GOOGL", "META", "NFLX", "JPM", "V",
    "BAC", "AMD", "PYPL", "DIS", "T", "PFE", "COST", "INTC", "KO", "TGT", "NKE",
    "SPY", "BA", "BABA", "XOM", "WMT", "GE", "CSCO", "VZ", "JNJ", "CVX", "PLTR",
    "SQ", "SHOP", "SBUX", "SOFI", "HOOD", "RBLX", "SNAP", "UBER", "FDX",
    "ABBV", "ETSY", "MRNA", "LMT", "GM", "F", "RIVN", "LCID", "CCL", "DAL", "UAL",
    "AAL", "TSM", "SONY", "ET", "NOK", "MRO", "COIN", "SIRI", "RIOT", "CPRX",
    "VWO", "SPYG", "ROKU", "VIAC", "ATVI", "BIDU", "DOCU", "ZM", "PINS", "TLRY",
    "WBA", "MGM", "NIO", "C", "GS", "WFC", "ADBE", "PEP", "UNH", "CARR", "FUBO",
    "HCA", "TWTR", "BILI", "RKT"
])

@tool(description="fetch stock data 5 years history using yfinance (yahoo).")
def get_stock_data(ticker):
    try:
            print(f"Fetching: {symbol}")
            hist = yf.Ticker(symbol).history(period="5y").reset_index()

            if hist.empty:
                print(f"- {symbol}: No data found.")
                return None

            # Add symbol column
            hist["Symbol"] = symbol
            return hist

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None