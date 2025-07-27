import requests
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv 


# Simple function to get most recent stock data


def get_ticker_data(ticker):
    load_dotenv()
    POLYGON_API_KEY= os.environ["POLYGON_API_KEY"]
    # Get date range for the last 200 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=200)
    
    # Format dates as YYYY-MM-DD
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


#data = get_ticker_data('AAPL')
#if data:
#    print(json.dumps(data, indent=2))
    
#data = get_ticker_data('I:NDX')
#if data:
#    print(json.dumps(data, indent=2))


        