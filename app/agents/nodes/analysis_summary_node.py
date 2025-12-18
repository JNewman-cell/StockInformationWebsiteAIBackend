"""
Analysis summary node - Summarizes significant news articles
"""

import logging
from typing import Dict, Any, List

from app.agents.state import AgentState
from app.agents.utils.llm_utils import call_llm_with_prompt

logger = logging.getLogger(__name__)


def get_summary_system_prompt() -> str:
    """Get the system prompt for news summarization"""
    return """You are an expert financial analyst specializing in concise stock price movement explanations.

Your task is to explain why a stock's price moved TODAY in 1-2 SENTENCES MAXIMUM.

**Focus on TODAY's movement:**
- Comment on regular market hours price change
- If after-hours data is provided, also comment on after-hours movement
- Connect the news articles to these specific price movements

**Format:**
[Stock ticker] went [up/down] [X]% today after [primary driver]. [After-hours: went [up/down] [X]% on [reason] / One brief supporting detail].

**Example 1 (with after-hours):**
Affirm stock went up 5.3% today after earnings surprised by 12%. After-hours, it gained another 2.1% as analysts upgraded their price targets.

**Example 2 (regular hours only):**
Tesla stock fell 3.2% today following reports of production delays at its Berlin facility.

**Requirements:**
- Maximum 1-2 sentences
- State TODAY's price direction and magnitude first (regular market)
- Include after-hours movement if data is provided
- Identify PRIMARY driver immediately after
- Add ONE supporting detail only if highly relevant
- Be direct, factual, and quantitative
- Use active, causal language

Return your explanation as plain text."""


def get_summary_user_prompt(
    ticker: str, 
    significant_articles: List[Dict[str, Any]],
    regular_market_change: float,
    post_market_change: float = None
) -> str:
    """Build the user prompt for summarization
    
    Args:
        ticker: Stock ticker symbol
        significant_articles: List of significant articles
        regular_market_change: Regular market hours price change percentage
        post_market_change: After-hours price change percentage (optional)
    """
    
    # Group articles by source
    company_articles = []
    index_articles = []
    peer_articles = []
    
    for article in significant_articles:
        source = article.get("source", "unknown")
        if source == ticker:
            company_articles.append(article)
        elif source in ["^GSPC", "^DJI", "^IXIC"]:
            index_articles.append(article)
        else:
            peer_articles.append(article)
    
    # Start with price movement data
    prompt = f"**Stock Ticker:** {ticker}\n\n"
    prompt += f"**TODAY's Price Movement:**\n"
    prompt += f"- Regular Market: {regular_market_change:+.2f}%\n"
    if post_market_change is not None:
        prompt += f"- After-Hours: {post_market_change:+.2f}%\n"
    prompt += f"\n**Total Significant Articles:** {len(significant_articles)}\n\n"
    
    if company_articles:
        prompt += f"### Company-Specific News ({len(company_articles)} articles)\n\n"
        for i, article in enumerate(company_articles, 1):
            prompt += f"{i}. **{article['title']}**\n"
            if article.get('summary'):
                prompt += f"   Summary: {article['summary']}\n"
            prompt += f"   Published: {article.get('published', 'N/A')}\n"
            prompt += f"   Significance: {article.get('significance', 'N/A')}\n\n"
    
    if index_articles:
        prompt += f"### Market/Index News ({len(index_articles)} articles)\n\n"
        for i, article in enumerate(index_articles, 1):
            prompt += f"{i}. **{article['title']}**\n"
            prompt += f"   Source: {article.get('source', 'N/A')}\n"
            if article.get('summary'):
                prompt += f"   Summary: {article['summary']}\n"
            prompt += f"   Published: {article.get('published', 'N/A')}\n"
            prompt += f"   Significance: {article.get('significance', 'N/A')}\n\n"
    
    if peer_articles:
        prompt += f"### Peer Company News ({len(peer_articles)} articles)\n\n"
        for i, article in enumerate(peer_articles, 1):
            prompt += f"{i}. **{article['title']}**\n"
            prompt += f"   Source: {article.get('source', 'N/A')}\n"
            if article.get('summary'):
                prompt += f"   Summary: {article['summary']}\n"
            prompt += f"   Published: {article.get('published', 'N/A')}\n"
            prompt += f"   Significance: {article.get('significance', 'N/A')}\n\n"
    
    prompt += f"\n**Task:** Write 1-2 sentences explaining {ticker}'s price movement TODAY.\n"
    prompt += f"Include regular market change ({regular_market_change:+.2f}%)"
    if post_market_change is not None:
        prompt += f" and after-hours change ({post_market_change:+.2f}%)"
    prompt += ".\n"
    prompt += f"Format: {ticker} went [up/down] [X]% today after [primary driver]. [After-hours detail if applicable].\n"
    prompt += "Be direct, factual, and quantitative."
    
    return prompt


def filter_significant_articles(significance_analysis: Dict[str, Any], threshold: float = 0.5) -> List[Dict[str, Any]]:
    """
    Filter articles with significance score above threshold
    
    Args:
        significance_analysis: Analysis results from analyze_news_significance_node
        threshold: Minimum significance score (default: 0.5)
        
    Returns:
        List of significant articles with metadata
    """
    significant_articles = []
    
    for source, analysis in significance_analysis.items():
        if not isinstance(analysis, dict):
            continue
            
        significance = analysis.get("significance", 0.0)
        
        if significance >= threshold:
            articles = analysis.get("articles", [])
            
            for article in articles:
                # Add source and significance to each article
                article_with_metadata = {
                    **article,
                    "source": source,
                    "significance": significance
                }
                significant_articles.append(article_with_metadata)
    
    # Sort by significance (highest first)
    significant_articles.sort(key=lambda x: x.get("significance", 0.0), reverse=True)
    
    return significant_articles


async def generate_summary_node(state: AgentState, model: str = "gpt-4o") -> AgentState:
    """
    Generate a summary of significant news articles
    
    Args:
        state: Current agent state with significance_analysis
        model: LLM model to use for summarization
        
    Returns:
        Updated state with news_summary
    """
    # Update progress immediately at start
    state["current_step"] = "generating_summary"
    state["progress_message"] = "Generating concise price movement explanation"
    
    logger.info("Starting summary generation...")
    
    try:
        ticker = state.get("ticker", "").upper()
        significance_analysis = state.get("significance_analysis", {})
        
        if not significance_analysis:
            logger.warning("No significance analysis found in state")
            state["news_summary"] = "No news analysis available."
            return state
        
        # Filter articles with significance > 0.5
        significant_articles = filter_significant_articles(significance_analysis, threshold=0.5)
        
        if not significant_articles:
            logger.info("No articles met significance threshold of 0.5")
            state["news_summary"] = f"No news articles were found to have significant relevance (>0.5 significance score) to {ticker}'s recent price movement."
            return state
        
        logger.info(f"Found {len(significant_articles)} significant articles for {ticker}")
        
        # Get price action data from state
        price_action_data = state.get("price_action_data", {})
        ticker_price = price_action_data.get("ticker", {})
        
        # Extract today's price movements
        regular_market_change = ticker_price.get("regular_market_change_percent", 0.0)
        post_market_change = ticker_price.get("post_market_change_percent")
        
        # Generate summary using LLM
        system_prompt = get_summary_system_prompt()
        user_prompt = get_summary_user_prompt(
            ticker=ticker,
            significant_articles=significant_articles,
            regular_market_change=regular_market_change,
            post_market_change=post_market_change
        )
        
        summary = await call_llm_with_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=0.3,
            response_format=None  # Plain text response
        )
        
        # Store summary in state
        state["news_summary"] = summary
        state["metadata"]["significant_articles_count"] = len(significant_articles)
        state["metadata"]["summary_generated"] = True
        
        state["progress_message"] = f"Generated summary from {len(significant_articles)} significant articles"
        logger.info(f"Successfully generated summary for {ticker}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in generate_summary_node: {e}", exc_info=True)
        state["error"] = f"Failed to generate news summary: {str(e)}"
        state["news_summary"] = f"Error generating summary: {str(e)}"
        return state
