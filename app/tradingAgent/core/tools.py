import requests
from datetime import datetime, timedelta
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

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username="itay601",
    )
    #print(reddit.read_only)
    reddit.read_only = True
    reddit_list = []
    for submission in reddit.subreddit("all").search(query, sort="top", time_filter="week", limit=100):
        submission.comments.replace_more(limit=0)
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

        