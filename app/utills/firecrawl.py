import os
from firecrawl import FirecrawlApp, ScrapeOptions
from dotenv import load_dotenv
import json

load_dotenv()

class FirecrawlService:
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("Missing FIRECRAWL_API_KEY environment variable")
        self.app = FirecrawlApp(api_key=api_key)

    def _serialize_result(self, result):
        """Convert firecrawl results to JSON-serializable format"""
        if not result:
            return None
        
        try:
            # If result is a dict, extract the relevant data
            if isinstance(result, dict):
                return {
                    'success': result.get('success', False),
                    'data': result.get('data', []),
                    'markdown': result.get('markdown', ''),
                    'metadata': result.get('metadata', {}),
                    'url': result.get('url', ''),
                    'content': result.get('content', ''),
                    'title': result.get('title', ''),
                    'description': result.get('description', '')
                }
            # If result is a list, process each item
            elif isinstance(result, list):
                return [self._serialize_result(item) for item in result]
            else:
                return str(result)
        except Exception as e:
            print(f"⚠️ Error serializing result: {e}")
            return {'error': str(e)}

    def search_financial_services(self, query: str, num_results: int = 5):
        """Search for financial services, tools, and market data providers"""
        try:
            financial_query = f"{query} financial market data API trading platform"
            result = self.app.search(
                query=financial_query,
                limit=num_results,
                scrape_options=ScrapeOptions(
                    formats=["markdown"]
                )
            )
            return self._serialize_result(result)
        except Exception as e:
            print(f"⚠️ Error searching financial services: {e}")
            return {'error': str(e)}

    def scrape_financial_website(self, url: str):
        """Scrape financial websites for detailed information"""
        try:
            result = self.app.scrape_url(
                url,
                formats=["markdown"],
                scrape_options=ScrapeOptions(
                    include_tags=["main", "article", "section", "div"],
                    exclude_tags=["nav", "footer", "header", "aside", "advertisement"]
                )
            )
            return self._serialize_result(result)
        except Exception as e:
            print(f"⚠️ Error scraping {url}: {e}")
            return {'error': str(e)}

    def search_market_data(self, query: str):
        """Search for specific market data about a stock symbol or financial instrument"""
        try:
            query2 = f"{query} price analysis financial data"
            result = self.app.search(
                query=query2,
                limit=3,
                scrape_options=ScrapeOptions(
                    formats=["markdown"]
                )
            )
            return self._serialize_result(result)
        except Exception as e:
            print(f"⚠️ Error searching market data for {query}: {e}")
            return {'error': str(e)}

    def scrape_economic_data(self, indicator: str):
        """Search for economic indicators and data"""
        try:
            query = f"{indicator} economic data statistics government source"
            result = self.app.search(
                query=query,
                limit=2,
                scrape_options=ScrapeOptions(
                    formats=["markdown"]
                )
            )
            return self._serialize_result(result)
        except Exception as e:
            print(f"⚠️ Error searching economic data for {indicator}: {e}")
            return {'error': str(e)}