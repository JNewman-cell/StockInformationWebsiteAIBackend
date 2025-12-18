"""
Prompt template for analyzing stock price movement significance
"""


def build_ticker_context(ticker: str, ticker_price: dict, ticker_news: list) -> str:
    """
    Build context section for the target ticker
    
    Args:
        ticker: Stock ticker symbol
        ticker_price: Price action data
        ticker_news: List of news articles
        
    Returns:
        Formatted context string
    """
    change_pct = ticker_price.get('regular_market_change_percent', 0) or 0
    volume = ticker_price.get('regular_market_volume')
    volume_str = f"{int(volume):,}" if isinstance(volume, (int, float)) else "N/A"
    
    context = f"""
# Stock: {ticker}

## Price Action
- Current Price: ${ticker_price.get('regular_market_price', 'N/A')}
- Change: ${ticker_price.get('regular_market_change', 'N/A')} ({change_pct:.2f}%)
- Previous Close: ${ticker_price.get('regular_market_previous_close', 'N/A')}
- Day Range: ${ticker_price.get('regular_market_day_low', 'N/A')} - ${ticker_price.get('regular_market_day_high', 'N/A')}
- Volume: {volume_str}

## Recent News for {ticker}
"""
    for i, article in enumerate(ticker_news[:10], 1):
        context += f"\n{i}. **{article.get('title', 'No title')}**\n"
        
        # Use full article text if available, otherwise use summary
        if article.get('text'):
            # Limit article text to 2000 chars to avoid token overflow
            article_text = article.get('text', '')[:2000]
            context += f"   Article: {article_text}\n"
            if len(article.get('text', '')) > 2000:
                context += f"   [Article truncated...]\n"
        elif article.get('summary'):
            context += f"   Summary: {article.get('summary', '')}\n"
    
    return context


def build_comparison_context(comparison_ticker: str, comparison_price: dict, comparison_news: list) -> str:
    """
    Build context section for a single comparison ticker (index or peer)
    
    Args:
        comparison_ticker: Ticker symbol for comparison
        comparison_price: Price action data
        comparison_news: List of news articles
        
    Returns:
        Formatted context string
    """
    change_pct = comparison_price.get('regular_market_change_percent', 0) or 0
    context = f"\n## Comparison: {comparison_ticker}\n"
    context += f"- Price: ${comparison_price.get('regular_market_price', 'N/A')}\n"
    context += f"- Change: ${comparison_price.get('regular_market_change', 'N/A')} ({change_pct:.2f}%)\n"
    
    if comparison_news:
        context += f"\n### Recent News for {comparison_ticker}\n"
        for i, article in enumerate(comparison_news[:10], 1):
            context += f"{i}. **{article.get('title', 'No title')}**\n"
            
            # Use full article text if available, otherwise use summary
            if article.get('text'):
                # Limit article text to 2000 chars to avoid token overflow
                article_text = article.get('text', '')[:2000]
                context += f"   Article: {article_text}\n"
                if len(article.get('text', '')) > 2000:
                    context += f"   [Article truncated...]\n"
            elif article.get('summary'):
                context += f"   Summary: {article.get('summary', '')}\n"
    
    return context


def get_analysis_prompt(
    ticker: str,
    ticker_context: str,
    comparison_ticker: str,
    comparison_context: str
) -> str:
    """
    Get the complete analysis prompt for comparing ticker against a single comparison source
    
    Args:
        ticker: Stock ticker symbol being analyzed
        ticker_context: Formatted ticker context
        comparison_ticker: Ticker being compared against (peer or index)
        comparison_context: Formatted comparison context
        
    Returns:
        Complete prompt string
    """
    return f"""Analyze how much {comparison_ticker}'s price movement and news influenced {ticker}'s price movement today.

{ticker_context}

{comparison_context}

**TASK**:
1. Use both PRICE CORRELATION and NEWS RELEVANCE to determine the significance of {comparison_ticker}'s influence on {ticker}.
2. Consider direction (sign) and magnitude (absolute %), relative vs absolute moves, and volume/volatility context.
3. Produce a JSON output that assigns a significance score (0.0–1.0) and returns the exact article objects (unchanged) that support the influence.

**RUBRIC FOR SIGNIFICANCE** (how to combine price + news):

**PRICE CORRELATION SCORE (0–1)**: Based on direction match + magnitude relative to comparison
- Directional mismatch → price score near 0
- Same direction, similar magnitude (within ±30%) → price score high (0.6–1.0)
- Same direction, much smaller magnitude → price score moderate (0.3–0.6)

**NEWS RELEVANCE SCORE (0–1)**: Presence of news that WOULD LOGICALLY IMPACT {ticker}
- Direct impact on {ticker} (for indices: Fed rates, economic data, geopolitical events; for peers: industry trends, sector regulations, competitor events) → high news score (0.7–1.0)
- Sector-wide or peer-specific news that indirectly affects {ticker} → moderate news score (0.4–0.7)
- No relevant articles → news score 0

**FINAL SIGNIFICANCE** = weighted combination: 0.6 * NEWS_RELEVANCE + 0.4 * PRICE_CORRELATION

**Significance Rating Scale (0.0 - 1.0)**:
- 0.0 - 0.2: No significant influence - {ticker}'s movement was not related to {comparison_ticker}
  Example: "MA's earnings report was not a significant factor in V's price movement today"
- 0.2 - 0.4: Minor influence - Some correlation but not a primary driver
- 0.4 - 0.6: Moderate influence - Notable correlation, partial driver
- 0.6 - 0.8: Strong influence - Clear correlation, major driver
- 0.8 - 1.0: Dominant influence - {ticker}'s movement was primarily determined by {comparison_ticker}
  Example: "V's price movement was primarily due to Fed interest rate cuts announced today (from S&P 500 news)"

**EDGE CASES**:
- Large move with NO NEWS (and no correlation to {comparison_ticker}): significance near 0; return empty article list
- Strong correlation with {comparison_ticker} but {comparison_ticker} has no specific news (only macro/general market): assign moderate-to-high significance (0.5-0.7) based on price correlation alone; explain that macro moves are likely the driver
- If {comparison_ticker}'s articles have timestamps older than {ticker}'s price movement by >24 hours, downweight their news relevance unless they are explicit ongoing events (e.g., delayed filing, multi-day regulatory action)

**RESPONSE FORMAT** (strict JSON):
Return a JSON object with this structure:
{{
    "{comparison_ticker}": {{
        "significance": <float between 0.0 and 1.0>,
        "articles": [
            // Include the full article objects that are most relevant to explaining {ticker}'s price movement
            // Each article MUST include: "title", "summary", "url", "publisher", "published_time", "source", and "text" fields
            // The "text" field contains the full extracted article content
            // Use the EXACT same format as provided in the comparison news
            // Only include articles that actually influenced {ticker}
            // If no articles are relevant, return empty array
        ]
    }}
}}

**IMPORTANT**: 
- Return the articles in the EXACT same format they were provided
- Each article MUST include the "text" field with the full article content
- Only include articles that are actually relevant to {ticker}'s price movement
- The significance must be calculated using the rubric above
- DO NOT hallucinate or invent article data
- DO NOT modify article text, titles, or summaries
"""


