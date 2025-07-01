import os
from firecrawl import FirecrawlApp, ScrapeOptions
from dotenv import load_dotenv

load_dotenv()


class FirecrawlService:
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("Missing FIRECRAWL_API_KEY environment variable")
        self.app = FirecrawlApp(api_key=api_key)

    def search_financial_services(self, query: str, num_results: int = 5):
        """Search for financial services, tools, and market data providers"""
        try:
            # Enhanced search query for financial content
            financial_query = f"{query} financial market data API trading platform"
            result = self.app.search(
                query=financial_query,
                limit=num_results,
                scrape_options=ScrapeOptions(
                    formats=["markdown"]
                )
            )
            return result
        except Exception as e:
            print(f"⚠️ Error searching financial services: {e}")
            return []

    def search_companies(self, query: str, num_results: int = 5):
        """Generic search method for backward compatibility"""
        return self.search_financial_services(query, num_results)

    def scrape_financial_website(self, url: str):
        """Scrape financial websites for detailed information"""
        try:
            result = self.app.scrape_url(
                url,
                formats=["markdown"],
                scrape_options=ScrapeOptions(
                    # Focus on content that's relevant to financial analysis
                    include_tags=["main", "article", "section", "div"],
                    exclude_tags=["nav", "footer", "header", "aside", "advertisement"]
                )
            )
            return result
        except Exception as e:
            print(f"⚠️ Error scraping {url}: {e}")
            return None

    def scrape_company_pages(self, url: str):
        """Backward compatibility method"""
        return self.scrape_financial_website(url)

    def search_market_data(self, symbol: str, data_type: str = "stock"):
        """Search for specific market data about a stock symbol or financial instrument"""
        try:
            query = f"{symbol} {data_type} price analysis financial data"
            result = self.app.search(
                query=query,
                limit=3,
                scrape_options=ScrapeOptions(
                    formats=["markdown"]
                )
            )
            return result
        except Exception as e:
            print(f"⚠️ Error searching market data for {symbol}: {e}")
            return []

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
            return result
        except Exception as e:
            print(f"⚠️ Error searching economic data for {indicator}: {e}")
            return []