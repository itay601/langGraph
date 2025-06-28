# Economic & Stocks Research Bot 📈

An intelligent research agent that helps you discover and analyze financial tools, market data providers, and investment platforms. Built with LangGraph, OpenAI, and Firecrawl for comprehensive financial research.

## 🚀 Features

- **Financial Tool Discovery**: Automatically finds and analyzes financial tools, trading platforms, and data providers
- **Market Data Analysis**: Searches for real-time and historical market data sources
- **Investment Platform Comparison**: Compares pricing models, features, and capabilities
- **API Integration Analysis**: Identifies financial APIs and their integration capabilities
- **Smart Recommendations**: Provides actionable insights based on your financial research needs

## 📊 What It Analyzes

### Financial Services & Tools
- Trading platforms (TradingView, Interactive Brokers, etc.)
- Market data providers (Yahoo Finance, Alpha Vantage, Bloomberg)
- Financial APIs and data feeds
- Investment analysis tools
- Portfolio management platforms

### Key Metrics Tracked
- **Pricing Models**: Free, Freemium, Paid, Enterprise
- **Market Coverage**: NYSE, NASDAQ, LSE, Crypto exchanges
- **Data Types**: Real-time vs delayed market data
- **Financial Metrics**: P/E ratios, RSI, MACD, Beta, ROI
- **Integration Capabilities**: API access, platform integrations
- **Asset Classes**: Stocks, bonds, crypto, forex, commodities

## 🛠️ Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd economic-stocks-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file:
```
FIRECRAWL_API_KEY=your_firecrawl_api_key
OPENAI_API_KEY=your_openai_api_key
```

4. **Run the bot**
```bash
python main.py
```

## 💡 Usage Examples

### Stock Analysis Tools
```
📈 Financial Query: best stock analysis tools with API access
```

### Market Data Providers
```
📈 Financial Query: real-time market data APIs for cryptocurrency
```

### Trading Platforms
```
📈 Financial Query: free trading platforms for beginners
```

### Economic Data Sources
```
📈 Financial Query: government economic indicators API
```

## 🏗️ Architecture

The bot uses a three-step research workflow:

1. **Extract Financial Tools** (`extract_financial_tools`)
   - Searches financial articles and resources
   - Identifies relevant tools and services
   - Filters for investment-related content

2. **Research Financial Services** (`research_financial_services`)
   - Scrapes official websites of identified tools
   - Extracts detailed feature information
   - Analyzes pricing and capabilities

3. **Analyze Investment Options** (`analyze_investment_options`)
   - Compares all researched options
   - Generates actionable recommendations
   - Provides cost-benefit analysis

## 🔧 Technical Stack

- **LangGraph**: Workflow orchestration and state management
- **OpenAI GPT-4**: Natural language processing and analysis
- **Firecrawl**: Web scraping and content extraction
- **Pydantic**: Data validation and structured outputs
- **Python 3.13**: Core programming language

## 📈 Data Models

### FinancialAnalysis
- Pricing models and cost structures
- Market coverage and data availability
- API access and integration options
- Real-time vs delayed data feeds

### CompanyInfo
- Service descriptions and capabilities
- Supported financial metrics
- Platform integrations
- Asset class coverage

## 🤖 AI-Powered Features

- **Structured Output**: Uses Pydantic models for consistent data extraction
- **Financial Context**: Specialized prompts for financial analysis
- **Smart Filtering**: Focuses on investment-relevant information
- **Comparative Analysis**: Generates side-by-side comparisons

## 🎯 Perfect For

- **Retail Investors**: Finding the right tools for personal investing
- **Financial Analysts**: Discovering new data sources and analysis tools
- **Developers**: Building financial applications and need API access
- **Trading Enthusiasts**: Comparing platforms and features
- **Researchers**: Analyzing economic data and market trends

## 🔒 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FIRECRAWL_API_KEY` | API key for web scraping service | Yes |
| `OPENAI_API_KEY` | OpenAI API key for LLM analysis | Yes |

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

**Disclaimer**: This tool is for research purposes only. Always verify financial information from official sources before making investment decisions.