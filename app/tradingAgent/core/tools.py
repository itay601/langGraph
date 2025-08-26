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
        return data
    except requests.exceptions.RequestException as error:
        print(f'Error fetching ticker data: {error}')
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
            return {"error": "No price data found."}
        latest = results[0]
        price = latest.get("c")  # 'c' is the close price
        time_unix = latest.get("t")
        time_str = datetime.fromtimestamp(time_unix / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        return {"symbol": symbol, "time": time_str, "price": price}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}




@tool(description="fetch stock data 5 years history using yfinance (yahoo).")
def get_stock_data_yahoo(ticker):
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
    for submission in reddit.subreddit("all").search(query, sort="top", time_filter="week", limit=5):
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
        #collection.insert_one(doc)
        #print(f"✅ Inserted post '{submission.title}' with {len(doc['comments'])} comments")
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




@tool(description="Save user portfolio to AstraDB")
def save_portfolio_to_astra(user_email: str, portfolio_data: dict, trade_results: dict = None):
    load_dotenv()
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

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
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

    # Initialize DataAPIClient
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    database = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)

    # Get collections
    users_collection = database.get_collection("users")
    portfolios_collection = database.get_collection("portfolios")
    trades_collection = database.get_collection("trades")
    """Get user portfolio from AstraDB by email"""
    try:
        # Find latest portfolio for user
        portfolio = portfolios_collection.find_one(
            {"user_email": user_email, "status": "active"},
            sort={"created_at": -1}
        )
        
        if portfolio:
            # Get recent trades
            recent_trades = list(trades_collection.find(
                {"user_email": user_email},
                sort={"timestamp": -1},
                limit=10
            ))
            
            return {
                "success": True,
                "portfolio": portfolio,
                "recent_trades": recent_trades
            }
        else:
            return {
                "success": False,
                "message": f"No portfolio found for user {user_email}"
            }
            
    except Exception as e:
        print(f"Error getting portfolio from AstraDB: {e}")
        return {
            "success": False,
            "error": str(e)
        }

tools_list = [
    get_ticker_data_poly,
    fetch_stock_price_polygon,
    get_stock_data_yahoo,
    get_reddit_vibe,
    get_related_articles,
    save_portfolio_to_astra,
    get_user_portfolio_from_astra
]
