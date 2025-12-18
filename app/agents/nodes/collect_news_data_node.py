"""
Collect news and price data node - fetches all data before analysis
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import httpx
from yahooquery import Ticker
import trafilatura

from app.agents.state import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def fetch_peers_from_fmp(ticker: str) -> List[str]:
    """
    Fetch peer companies from Financial Modeling Prep API
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List of peer ticker symbols
    """
    try:
        # Check if API key is configured
        if not settings.fmp_api_key:
            logger.info(f"FMP API key not configured, skipping peer discovery for {ticker}")
            return []
        
        # Use the correct FMP endpoint for stock peers
        url = f"https://financialmodelingprep.com/stable/stock-peers?symbol={ticker}&apikey={settings.fmp_api_key}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # FMP returns format: [{"symbol": "GOOGL", "companyName": "...", "price": ..., "mktCap": ...}, ...]
            if isinstance(data, list) and len(data) > 0:
                # Extract just the symbols and limit to top 3 peers by market cap
                peers_with_cap = [(item.get("symbol"), item.get("mktCap", 0)) for item in data if item.get("symbol")]
                # Sort by market cap descending and take top 3
                peers_with_cap.sort(key=lambda x: x[1], reverse=True)
                peers_list = [symbol for symbol, _ in peers_with_cap[:3]]
                
                if peers_list:
                    logger.info(f"Found {len(peers_list)} peers for {ticker}: {peers_list}")
                    return peers_list
            
            logger.info(f"No peers found for {ticker} from FMP")
            return []
            
    except Exception as e:
        logger.warning(f"Could not fetch peers from FMP for {ticker}: {e}")
        return []


def get_article_identifiers(news_articles: List[Dict[str, Any]]) -> set:
    """
    Create a set of article identifiers (URLs and titles) for deduplication
    
    Args:
        news_articles: List of news article dictionaries
        
    Returns:
        Set of identifiers (URLs and normalized titles)
    """
    identifiers = set()
    for article in news_articles:
        # Add URL as identifier
        url = article.get('url', '')
        if url:
            identifiers.add(url)
        
        # Add normalized title as identifier (lowercase, stripped)
        title = article.get('title', '').lower().strip()
        if title:
            identifiers.add(title)
    
    return identifiers


def filter_duplicate_articles(articles: List[Dict[str, Any]], existing_identifiers: set) -> List[Dict[str, Any]]:
    """
    Filter out articles that already exist in the existing_identifiers set
    
    Args:
        articles: List of news articles to filter
        existing_identifiers: Set of existing article identifiers (URLs and titles)
        
    Returns:
        Filtered list of articles
    """
    filtered = []
    for article in articles:
        url = article.get('url', '')
        title = article.get('title', '').lower().strip()
        
        # Check if article is already in existing set
        if url not in existing_identifiers and title not in existing_identifiers:
            filtered.append(article)
        else:
            logger.debug(f"Filtering duplicate article: {article.get('title', 'No title')}")
    
    return filtered


async def extract_article_text(url: str) -> Optional[str]:
    """
    Extract full article text from URL using trafilatura
    
    Args:
        url: Article URL
        
    Returns:
        Extracted article text or None if extraction fails
    """
    try:
        # Fetch and extract in executor since trafilatura is synchronous
        loop = asyncio.get_event_loop()
        downloaded = await loop.run_in_executor(None, trafilatura.fetch_url, url)
        
        if not downloaded:
            return None
            
        text = await loop.run_in_executor(None, trafilatura.extract, downloaded)
        return text
        
    except Exception as e:
        logger.debug(f"Could not extract text from {url}: {e}")
        return None


async def fetch_news_from_yahoo(ticker: str, count: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch news articles for a given ticker using yahooquery (async)
    
    Args:
        ticker: Stock ticker symbol
        count: Number of news articles to fetch
        
    Returns:
        List of news articles
    """
    try:
        # Run yahooquery in executor since it's synchronous
        loop = asyncio.get_event_loop()
        yq_ticker = Ticker(ticker)
        news = await loop.run_in_executor(None, lambda: yq_ticker.news(count=count))
        
        # Check for errors - yahooquery returns ['error'] when API fails
        if news == ['error'] or not news:
            logger.warning(f"Yahoo Finance API returned error or no news for {ticker}")
            return []
        
        # Handle yahooquery response format - it returns dict with ticker as key
        if isinstance(news, dict):
            # Get news array from dict (ticker is the key)
            news = news.get(ticker, [])
        
        if not isinstance(news, list):
            logger.warning(f"Unexpected news format for {ticker}: {type(news)}")
            return []
        
        # Format news data and extract article text
        formatted_news = []
        for article in news:
            if isinstance(article, dict):
                # Filter: only include articles with contentType = "STORY"
                content_type = article.get("contentType", "")
                if content_type != "STORY":
                    logger.debug(f"Skipping non-STORY content type: {content_type} - {article.get('title', 'No title')}")
                    continue
                
                # Get canonical URL or fallback to link/url
                canonical_url = None
                if "canonicalUrl" in article and isinstance(article["canonicalUrl"], dict):
                    canonical_url = article["canonicalUrl"].get("url")
                
                article_url = canonical_url or article.get("link", article.get("url", ""))
                
                # Extract full article text
                article_text = await extract_article_text(article_url) if article_url else None
                
                formatted_news.append({
                    "title": article.get("title", ""),
                    "summary": article.get("summary", ""),
                    "url": article_url,
                    "publisher": article.get("publisher", article.get("provider_name", "")),
                    "published_time": datetime.fromtimestamp(article.get("providerPublishTime", article.get("provider_publish_time", 0))).isoformat() if article.get("providerPublishTime", article.get("provider_publish_time")) else None,
                    "source": ticker,
                    "text": article_text  # Full article text
                })
        
        return formatted_news
        
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []


async def fetch_price_action(tickers: List[str]) -> Dict[str, Any]:
    """
    Fetch current and previous day price action for given tickers (async)
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Dictionary with price action data for each ticker
    """
    try:
        # Run in executor since yahooquery is synchronous
        loop = asyncio.get_event_loop()
        
        # Fetch each ticker individually to handle response format better
        price_data = {}
        
        for ticker in tickers:
            yq_ticker = Ticker(ticker)
            quotes = await loop.run_in_executor(None, lambda t=ticker: Ticker(t).quotes)
            
            # yahooquery returns dict with ticker as key, or list with single item
            if isinstance(quotes, dict) and ticker in quotes:
                quote = quotes[ticker]
            elif isinstance(quotes, list) and len(quotes) > 0:
                quote = quotes[0]
            else:
                logger.warning(f"No quote found for {ticker}")
                continue
            
            if not isinstance(quote, dict):
                logger.warning(f"Invalid quote data for {ticker}")
                continue
            
            price_data[ticker] = {
                "symbol": quote.get("symbol"),
                "regular_market_price": quote.get("regularMarketPrice"),
                "regular_market_change": quote.get("regularMarketChange"),
                "regular_market_change_percent": quote.get("regularMarketChangePercent"),
                "regular_market_previous_close": quote.get("regularMarketPreviousClose"),
                "regular_market_open": quote.get("regularMarketOpen"),
                "regular_market_day_high": quote.get("regularMarketDayHigh"),
                "regular_market_day_low": quote.get("regularMarketDayLow"),
                "regular_market_volume": quote.get("regularMarketVolume"),
                "post_market_price": quote.get("postMarketPrice"),
                "post_market_change": quote.get("postMarketChange"),
                "post_market_change_percent": quote.get("postMarketChangePercent"),
                "fifty_two_week_high": quote.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": quote.get("fiftyTwoWeekLow"),
                "market_cap": quote.get("marketCap"),
                "timestamp": datetime.now().isoformat()
            }
        
        return price_data
        
    except Exception as e:
        logger.error(f"Error fetching price action: {e}")
        return {}


async def collect_news_data_node(state: AgentState) -> AgentState:
    """
    Collect news and price action data for ticker, market indices, and peers.
    This node only collects data - analysis is done in the next node.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with news data and price action
    """
    try:
        ticker = state.get("ticker", "").upper()
        if not ticker:
            state["error"] = "No ticker provided"
            return state
        
        # Update progress immediately at start
        state["current_step"] = "collecting_news"
        state["progress_message"] = "Collecting current news articles and stock price movement"
        
        logger.info(f"Collecting news and price data for {ticker}")
        
        # Define market indices
        indices = ["^GSPC", "^DJI", "^IXIC"]  # S&P 500, Dow Jones, NASDAQ
        
        # Step 1: Fetch index news FIRST (these have priority for deduplication)
        state["progress_message"] = "Fetching news from market indices (S&P 500, Dow Jones, NASDAQ)"
        logger.info(f"Fetching market index news first")
        index_news_tasks = [fetch_news_from_yahoo(idx, count=10) for idx in indices]
        index_news_results = await asyncio.gather(*index_news_tasks, return_exceptions=True)
        
        # Parse index news results
        market_news = {}
        for i, index in enumerate(indices):
            result = index_news_results[i]
            market_news[index] = result if not isinstance(result, Exception) else []
        
        # Build set of article identifiers from index news for deduplication
        index_article_identifiers = set()
        for articles in market_news.values():
            index_article_identifiers.update(get_article_identifiers(articles))
        
        logger.info(f"Found {len(index_article_identifiers)} unique articles from indices")
        
        # Step 2: Fetch peers and ticker news in parallel
        state["progress_message"] = f"Discovering peer companies and fetching news for {ticker}"
        logger.info(f"Fetching peers and individual stock news")
        peers_task = fetch_peers_from_fmp(ticker)
        ticker_news_task = fetch_news_from_yahoo(ticker, count=10)
        
        peers, ticker_news_raw = await asyncio.gather(peers_task, ticker_news_task)
        state["peers"] = peers
        logger.info(f"Found peers: {peers}")
        
        # Filter ticker news to remove duplicates from index news
        ticker_news = filter_duplicate_articles(ticker_news_raw, index_article_identifiers)
        logger.info(f"Ticker news: {len(ticker_news_raw)} articles -> {len(ticker_news)} after deduplication")
        
        # Step 3: Collect news for peers in parallel
        peer_news = {}
        if peers:
            state["progress_message"] = f"Fetching news from {len(peers)} peer companies: {', '.join(peers)}"
            logger.info(f"Collecting news for {len(peers)} peers")
            peer_news_tasks = [fetch_news_from_yahoo(peer, count=10) for peer in peers]
            peer_news_results = await asyncio.gather(*peer_news_tasks, return_exceptions=True)
            
            # Filter peer news to remove duplicates from index news
            for i, peer in enumerate(peers):
                result = peer_news_results[i]
                raw_articles = result if not isinstance(result, Exception) else []
                filtered_articles = filter_duplicate_articles(raw_articles, index_article_identifiers)
                peer_news[peer] = filtered_articles
                logger.info(f"Peer {peer} news: {len(raw_articles)} articles -> {len(filtered_articles)} after deduplication")
        
        logger.info(f"Collected news: {len(ticker_news)} for {ticker}, "
                   f"{sum(len(v) for v in market_news.values())} for indices, "
                   f"{sum(len(v) for v in peer_news.values())} for peers")
        
        # Store all news data
        state["news_data"] = {
            "ticker": ticker_news,
            "market": market_news,
            "peers": peer_news,
            "collected_at": datetime.now().isoformat()
        }
        
        # Step 4: Collect price action for all tickers in parallel
        state["progress_message"] = "Fetching current stock prices and market data"
        logger.info("Collecting price action data")
        all_tickers = [ticker] + indices
        if peers:
            all_tickers.extend(peers)
        all_price_data = await fetch_price_action(all_tickers)
        
        # Organize price data
        ticker_price = all_price_data.get(ticker, {})
        market_prices = {idx: all_price_data.get(idx, {}) for idx in indices}
        peer_prices = {peer: all_price_data.get(peer, {}) for peer in peers} if peers else {}
        
        state["price_action_data"] = {
            "ticker": ticker_price,
            "market": market_prices,
            "peers": peer_prices,
            "collected_at": datetime.now().isoformat()
        }
        
        # Update metadata
        state["metadata"]["news_collected"] = True
        state["metadata"]["news_count"] = {
            "ticker": len(ticker_news),
            "market": {idx: len(market_news.get(idx, [])) for idx in indices},
            "peers": {peer: len(peer_news.get(peer, [])) for peer in peers}
        }
        state["metadata"]["peers_discovered"] = len(peers)
        
        total_articles = len(ticker_news) + sum(len(v) for v in market_news.values()) + sum(len(v) for v in peer_news.values())
        state["progress_message"] = f"Collected {total_articles} articles from {len(peers) + len(indices) + 1} sources"
        logger.info(f"Successfully collected all data for {ticker}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in collect_news_data_node: {e}", exc_info=True)
        state["error"] = f"Failed to collect news and price data: {str(e)}"
        return state
