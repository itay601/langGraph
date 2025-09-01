import requests
from datetime import datetime, timedelta, timezone
import json
import os
from dotenv import load_dotenv 
import yfinance as yf
from langchain_core.tools import tool 
import praw
from astrapy import DataAPIClient
import time
import re
import time
from typing import Optional, Dict, List

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

@tool(description="fetch stock data 200 days history using polygone.")
def get_ticker_data_poly(ticker):
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
        time.sleep(1)
        return data
    except requests.exceptions.RequestException as error:
        print(f'Error fetching ticker data: {error}')
        time.sleep(1)
        return None

@tool(description="fetch latest(current) stock price using polygon.")
def fetch_stock_price_polygon(symbol: str):
    load_dotenv()
    api_key = os.getenv("POLYGON_API_KEY")
    """Fetch the latest stock price for a given symbol from Polygon.io."""
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        results = data.get("results")
        if not results or len(results) == 0:
            time.sleep(1)
            return {"error": "No price data found."}
        latest = results[0]
        price = latest.get("c")  # 'c' is the close price
        time_unix = latest.get("t")
        time_str = datetime.fromtimestamp(time_unix / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        time.sleep(1)
        return {"symbol": symbol, "time": time_str, "price": price}
    except requests.exceptions.RequestException as e:
        time.sleep(1)
        return {"error": str(e)}




@tool(description="fetch stock data 5 years history using yfinance (yahoo).")
def get_stock_data_yahoo(ticker):
    try:
            print(f"Fetching: {ticker}")
            hist = yf.Ticker(ticker).history(period="5y").reset_index()

            if hist.empty:
                print(f"- {ticker}: No data found.")
                return None

            # Add symbol column
            hist["Symbol"] = ticker
            return hist

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None




@tool(description="fetch reddit posts and comments related to stocks and economic terms.(query of user choice)")
def get_reddit_vibe(query):
    load_dotenv()
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_KEY")
    user_agent = "testscript by u/fakebot3"

    reddit = praw.Reddit(    # change to -- asyncpraw
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username="itay601",
    )
    reddit.read_only = True
    reddit_list = []
    for submission in reddit.subreddit("all").search(query, sort="top", time_filter="week", limit=3):
        submission.comments.replace_more(limit=0)
        
        top_comments = []
        for comment in submission.comments:
            top_comments.append(comment)

        top_comments = sorted(submission.comments, key=lambda c: c.score, reverse=True)

        # Insert submission and comments into list 
        doc = {
            "query": query,
            "title": submission.title,
            "score": submission.score,
            "url": submission.url,
            "subreddit": str(submission.subreddit),
            "comments": [
                {"body": c.body, "score": c.score}
                for c in top_comments[:5]
            ],
        }
        reddit_list.append(doc)
    return reddit_list
    


@tool(description="fetch articles from all economic sources related to companies.(use it if for each company you want to get related articles)")
def get_related_articles(ticker):
    load_dotenv()
    url = os.getenv("URL_ARTICLES")  
    headers = {"Content-Type": "application/json"}
    # You can filter articles by ticker if the API supports it, but here we use the provided query
    payload = {
        "query": "{ articles { id source_name author title description url urlToImage content economic_terms createdAt } }"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("articles", [])
    except Exception as e:
        print(f"Error fetching articles: {e}")
        return None



@tool(description="Set user portfolio from AstraDB")
def build_user_portfolio_from_astra(
    user_email: str,
    research_results: Dict,
):
    load_dotenv()
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_TOKEN")
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_ENDPOINT")

    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    database = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
    portfolios_collection = database.get_collection("portfolios")

    # Build update fields
    update_fields = {
        "user_email": user_email,
        "ticker": None,
        "latest_price": None,
        "yahoo_data": None,
        "polygon_data": None,
        "reddit_sentiment": None,
        "news_articles": None,
        "date": datetime.utcnow().isoformat()
    }
    try:
        if ticker:
            update_fields["ticker"] = research_results["ticker"]
        if latest_price is not None:
            update_fields["latest_price"] = research_results["latest_price"]
        if yahoo_data:
            update_fields["yahoo_data"] =research_results["yahoo_data"] 
        if polygon_data:
            update_fields["polygon_data"] =research_results["polygon_data"] 
        if reddit_sentiment:
            update_fields["reddit_sentiment"] =research_results["reddit_sentiment"] 
        if news_articles:
            update_fields["news_articles"] = research_results["news_articles"]
        

    
        # Upsert by (user_email, ticker)
        filter_query = {"user_email": user_email}
        if ticker:
            filter_query["ticker"] = ticker

        # Upsert each field individually to avoid overwriting existing data
        portfolios_collection.update_one(
            filter_query,
            {"$set": {"ticker":update_fields["ticker"]}},
            upsert=True
        )
        portfolios_collection.update_one(
            filter_query,
            {"$set": {"latest_price": update_fields["latest_price"]}},
            upsert=True
        )
        portfolios_collection.update_one(
            filter_query,
            {"$set": {"yahoo_data": update_fields["yahoo_data"]}},
            upsert=True
        )
        portfolios_collection.update_one(
            filter_query,
            {"$set": {"polygon_data": update_fields["polygon_data"]}},
            upsert=True
        )
        portfolios_collection.update_one(
            filter_query,
            {"$set": {"reddit_sen": update_fields["reddit_sentiment"]}},
            upsert=True
        )
        portfolios_collection.update_one(
            filter_query,
            {"$set": {"news": update_fields["news_articles"]}},
            upsert=True
        )
        portfolios_collection.update_one(
            filter_query,
            {"$set": update_fields["date"]},
            upsert=True
        )
        return portfolios_collection.find_one(filter_query)

    except Exception as e:
        return {"error": str(e)}

@tool(description="Save user portfolio to AstraDB")
def save_portfolio_to_astra(user_email: str, portfolio_data: dict, trade_results: dict = None):
    load_dotenv()
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_TOKEN")
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_ENDPOINT")

    # Initialize DataAPIClient
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    database = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)

    # Get collections
    users_collection = database.get_collection("users")
    portfolios_collection = database.get_collection("portfolios")
    trades_collection = database.get_collection("trades")
    """Save user portfolio to AstraDB by email"""
    try:
        # First, ensure user exists
        user_doc = users_collection.find_one({"email": user_email})
        if not user_doc:
            # Create new user
            user_doc = {
                "_id": str(uuid.uuid4()),
                "email": user_email,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat()
            }
            users_collection.insert_one(user_doc)
        
        # Save portfolio
        portfolio_doc = {
            "_id": str(uuid.uuid4()),
            "user_id": user_doc["_id"],
            "user_email": user_email,
            "portfolio_allocation": portfolio_data.get("portfolio_allocation", {}),
            "execution_plan": portfolio_data.get("execution_plan", {}),
            "budget": portfolio_data.get("budget", 0),
            "strategy": portfolio_data.get("strategy", ""),
            "risk_level": portfolio_data.get("risk_level", "medium"),
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # Insert portfolio
        result = portfolios_collection.insert_one(portfolio_doc)
        
        # Save trade results if provided
        if trade_results:
            trade_doc = {
                "_id": str(uuid.uuid4()),
                "portfolio_id": portfolio_doc["_id"],
                "user_email": user_email,
                "trade_results": trade_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            trades_collection.insert_one(trade_doc)
        
        return {
            "success": True,
            "portfolio_id": portfolio_doc["_id"],
            "message": f"Portfolio saved successfully for user {user_email}"
        }
        
    except Exception as e:
        print(f"Error saving portfolio to AstraDB: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@tool(description="Get user portfolio from AstraDB")
def get_user_portfolio_from_astra(user_email: str):
    load_dotenv()
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_TOKEN")
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_ENDPOINT")

    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    database = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
    portfolios_collection = database.get_collection("portfolios")
    portfolio = portfolios_collection.find_one({"user_email": user_email})
    if portfolio:
        return portfolio
    else:
        return {"error": "Portfolio not found."}
    

def extract_symbols(response_text):
    """
    Extracts stock/crypto symbols from a trading plan response string.
    
    Args:
        response_text (str): The full response string containing the FINAL TRADING PLAN OUTPUT JSON.
    
    Returns:
        list: A list of extracted symbols (e.g., ['BTC-USD', 'ETH-USD']).
    """
    # Try to match the JSON between "FINAL TRADING PLAN OUTPUT:" and "Database Status:"
    match = re.search(r'FINAL TRADING PLAN OUTPUT:\s*(\{.*?\})\s*Database Status:', response_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: Find content between first '{' after marker and last '}' in the string
        marker = "FINAL TRADING PLAN OUTPUT:"
        if marker in response_text:
            start = response_text.find(marker) + len(marker)
            brace_start = response_text.find('{', start)
            brace_end = response_text.rfind('}')
            if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
                json_str = response_text[brace_start:brace_end+1]
            else:
                return []
        else:
            return []

    try:
        plan_json = json.loads(json_str)
        allocations = plan_json.get('execution_summary', {}).get('stock_allocations', [])
        symbols = [alloc.get('symbol') for alloc in allocations if alloc.get('symbol')]
        return symbols
    except json.JSONDecodeError:
        return []


## Purpose
# ['BTC-ISR', 'USD-BTC'] --> ['BTC', 'USD']
def extract_symbols_list(comp_list):
    symbols = []
    for item in comp_list:
        parts = item.split("-")
        if parts:  # make sure it's not empty
            symbols.append(parts[0].strip())
    return symbols




tools_list = [
    get_ticker_data_poly,
    fetch_stock_price_polygon,
    get_stock_data_yahoo,
    get_reddit_vibe,
    get_related_articles,
    build_user_portfolio_from_astra,
    get_user_portfolio_from_astra,
    save_portfolio_to_astra
]
