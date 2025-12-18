"""
Prompt template for analyzing company-specific news significance on stock price movement
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


def get_company_analysis_prompt(
    ticker: str,
    ticker_context: str,
    change_percent: float = 0.0
) -> str:
    """
    Get the complete analysis prompt for company-specific news significance
    
    Args:
        ticker: Stock ticker symbol being analyzed
        ticker_context: Formatted ticker context with price and news
        change_percent: Price change percentage for context
        
    Returns:
        Complete prompt string
    """
    return f"""Analyze how much {ticker}'s own news and company-specific events influenced its price movement today.

{ticker_context}

**TASK**:
1. Evaluate the COMPANY-SPECIFIC NEWS to determine how much {ticker}'s own announcements and events caused the observed price movement.
2. Consider the type, magnitude, and timing of the news relative to the {change_percent:.2f}% price change.
3. Produce a JSON output that assigns a significance score (0.0–1.0) and returns the exact article objects (unchanged) that support the influence.

**RUBRIC FOR SIGNIFICANCE**:

**NEWS IMPACT ASSESSMENT (0–1)**:
Evaluate the inherent importance and potential market impact of the news:
- Major earnings beats/misses, guidance changes → high impact (0.7–1.0)
- Product launches, M&A announcements, CEO changes → high impact (0.7–1.0)
- Regulatory actions, major lawsuits, recalls → high impact (0.6–0.9)
- Analyst upgrades/downgrades, partnerships → moderate impact (0.4–0.7)
- Routine announcements, minor updates → low impact (0.1–0.3)
- No significant news → impact near 0

**PRICE MAGNITUDE VALIDATION (0–1)**:
Does the news justify the observed {change_percent:.2f}% price change?
- Large news + large price move (>3%) → validation high (0.8–1.0)
- Large news + moderate move (1-3%) → validation moderate (0.5–0.7)
- Large news + small move (<1%) → validation low (0.3–0.5)
- Minor news + any price move → validation low (0.2–0.4)
- No news + any price move → validation near 0

**FINAL SIGNIFICANCE** = weighted combination: 0.6 * NEWS_IMPACT + 0.4 * PRICE_VALIDATION

**Significance Rating Scale (0.0 - 1.0)**:
- 0.0 - 0.2: No significant company news - Price movement was likely driven by external factors (market/sector)
  Example: "V had only routine announcements today, no significant news to explain the price movement"
- 0.2 - 0.4: Minor company news - Some news but not substantial enough to be a primary driver
  Example: "AAPL announced minor product update, insufficient to explain 2% price movement"
- 0.4 - 0.6: Moderate company news - Notable announcements that partially explain the price movement
  Example: "MSFT partnership announcement is relevant but doesn't fully explain the 1.5% gain"
- 0.6 - 0.8: Strong company news - Significant company events that are major drivers
  Example: "AAPL announced new iPhone launch date and Q4 earnings beat expectations"
- 0.8 - 1.0: Dominant company news - Major company-specific events that fully explain the price movement
  Example: "TSLA announced CEO transition and major product recall affecting 50% of vehicles"

**EDGE CASES**:
- Large price move with NO COMPANY NEWS: significance near 0; return empty article list; note that external factors (market/sector) likely drove the move
- Multiple moderate news items: aggregate their impact; if 3+ moderate items align, can reach high significance (0.6-0.8)
- News with timestamps >24 hours old: downweight significance unless it's ongoing (multi-day regulatory action, delayed market reaction)
- Pre-market or after-hours news: if article is within 12 hours of price movement, treat as relevant

**RESPONSE FORMAT** (strict JSON):
Return a JSON object with this structure:
{{
    "{ticker}": {{
        "significance": <float between 0.0 and 1.0>,
        "articles": [
            // Include the full article objects that are most relevant to explaining {ticker}'s price movement
            // Each article MUST include ALL fields: "title", "summary", "url", "publisher", "published_time", "source", and "text"
            // The "text" field contains the full extracted article content - DO NOT omit this field
            // Use the EXACT same format as provided in the news data
            // Only include articles that actually influenced the price movement
            // If no articles are relevant, return empty array
        ]
    }}
}}

**IMPORTANT**: 
- Return the articles in the EXACT same format they were provided
- Each article MUST include the "text" field with the full article content
- Only include articles that are actually relevant to {ticker}'s price movement
- The significance must be calculated using the rubric above (NEWS_IMPACT + PRICE_VALIDATION)
- DO NOT hallucinate or invent article data
- DO NOT modify article text, titles, or summaries
"""
