"""
Analyze news significance node - performs LLM analysis on collected news data
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import asyncio

from app.agents.state import AgentState
from app.agents.utils.llm_utils import call_llm_with_prompt
from app.agents.prompts.price_significance_analysis_prompt import (
    build_ticker_context,
    build_comparison_context,
    get_analysis_prompt
)
from app.agents.prompts.company_specific_analysis_prompt import (
    build_ticker_context as build_company_ticker_context,
    get_company_analysis_prompt
)
from app.agents.prompts.news_analysis_system_prompt import get_news_analysis_system_prompt

logger = logging.getLogger(__name__)


def batch_articles(articles: List[Dict[str, Any]], batch_size: int = 5) -> List[List[Dict[str, Any]]]:
    """
    Split articles into batches of specified size
    
    Args:
        articles: List of article dictionaries
        batch_size: Maximum articles per batch (default: 5)
        
    Returns:
        List of article batches
    """
    if not articles:
        return []
    
    batches = []
    for i in range(0, len(articles), batch_size):
        batches.append(articles[i:i + batch_size])
    
    return batches


async def analyze_comparison(
    ticker: str,
    ticker_news: List[Dict[str, Any]],
    ticker_price: Dict[str, Any],
    comparison_ticker: str,
    comparison_news: List[Dict[str, Any]],
    comparison_price: Dict[str, Any],
    model: str = "gpt-5-nano"
) -> Dict[str, Any]:
    """
    Analyze how a single comparison ticker (peer or index) influences the main ticker's price movement.
    Batches articles into groups of 5 max, sends each batch to LLM, then aggregates results.
    
    Args:
        ticker: The stock ticker being analyzed
        ticker_news: News articles for the ticker
        ticker_price: Price action data for the ticker
        comparison_ticker: The ticker to compare against (peer or index)
        comparison_news: News articles for the comparison ticker
        comparison_price: Price action data for the comparison ticker
        model: OpenAI model to use for analysis (default: gpt-5-nano)
        
    Returns:
        Dictionary with significance analysis in format:
        {
            "comparison_ticker": {
                "significance": 0.0-1.0,
                "articles": [list of relevant articles]
            }
        }
    """
    try:
        # If no comparison news, return zero significance
        if not comparison_news:
            return {
                comparison_ticker: {
                    "significance": 0.0,
                    "articles": []
                }
            }
        
        # Batch comparison news into groups of 5
        news_batches = batch_articles(comparison_news, batch_size=5)
        logger.info(f"Analyzing {ticker} vs {comparison_ticker}: {len(comparison_news)} articles split into {len(news_batches)} batches")
        
        # Build ticker context once (doesn't change per batch)
        ticker_context = build_ticker_context(ticker, ticker_price, ticker_news)
        system_prompt = get_news_analysis_system_prompt()
        
        # Analyze each batch
        batch_tasks = []
        for batch_idx, news_batch in enumerate(news_batches):
            comparison_context = build_comparison_context(comparison_ticker, comparison_price, news_batch)
            user_prompt = get_analysis_prompt(ticker, ticker_context, comparison_ticker, comparison_context)
            
            task = call_llm_with_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=1
            )
            batch_tasks.append(task)
        
        # Execute all batch analyses in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Aggregate results
        significance_scores = []
        all_significant_articles = []
        
        for batch_idx, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Error in batch {batch_idx} for {ticker} vs {comparison_ticker}: {result}")
                continue
            
            # Extract significance and articles from batch result
            if isinstance(result, dict) and comparison_ticker in result:
                batch_data = result[comparison_ticker]
                significance = batch_data.get("significance", 0.0)
                articles = batch_data.get("articles", [])
                
                significance_scores.append(significance)
                all_significant_articles.extend(articles)
        
        # Calculate average significance across all batches
        avg_significance = sum(significance_scores) / len(significance_scores) if significance_scores else 0.0
        
        logger.info(f"Completed {len(batch_results)} batches for {comparison_ticker}: avg significance = {avg_significance:.3f}, {len(all_significant_articles)} significant articles")
        
        return {
            comparison_ticker: {
                "significance": avg_significance,
                "articles": all_significant_articles
            }
        }
        
    except Exception as e:
        logger.error(f"Error in comparison analysis for {ticker} vs {comparison_ticker}: {e}")
        return {
            comparison_ticker: {
                "significance": 0.0,
                "articles": [],
                "error": str(e)
            }
        }


async def analyze_company_specific(
    ticker: str,
    ticker_news: List[Dict[str, Any]],
    ticker_price: Dict[str, Any],
    model: str = "gpt-5-nano"
) -> Dict[str, Any]:
    """
    Analyze how the ticker's own company-specific news influences its price movement.
    Batches articles into groups of 5 max, sends each batch to LLM, then aggregates results.
    
    Args:
        ticker: The stock ticker being analyzed
        ticker_news: News articles for the ticker
        ticker_price: Price action data for the ticker
        model: OpenAI model to use for analysis (default: gpt-5-nano)
        
    Returns:
        Dictionary with significance analysis in format:
        {
            "ticker": {
                "significance": 0.0-1.0,
                "articles": [list of relevant articles]
            }
        }
    """
    try:
        # If no ticker news, return zero significance
        if not ticker_news:
            return {
                ticker: {
                    "significance": 0.0,
                    "articles": []
                }
            }
        
        # Batch ticker news into groups of 5
        news_batches = batch_articles(ticker_news, batch_size=5)
        logger.info(f"Analyzing {ticker} company-specific news: {len(ticker_news)} articles split into {len(news_batches)} batches")
        
        # Get system prompt and price change (same for all batches)
        system_prompt = get_news_analysis_system_prompt()
        change_percent = ticker_price.get('regular_market_change_percent', 0.0)
        
        # Analyze each batch
        batch_tasks = []
        for batch_idx, news_batch in enumerate(news_batches):
            ticker_context = build_company_ticker_context(ticker, ticker_price, news_batch)
            user_prompt = get_company_analysis_prompt(ticker, ticker_context, change_percent)
            
            task = call_llm_with_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=1
            )
            batch_tasks.append(task)
        
        # Execute all batch analyses in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Aggregate results
        significance_scores = []
        all_significant_articles = []
        
        for batch_idx, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Error in batch {batch_idx} for {ticker} company-specific: {result}")
                continue
            
            # Extract significance and articles from batch result
            if isinstance(result, dict) and ticker in result:
                batch_data = result[ticker]
                significance = batch_data.get("significance", 0.0)
                articles = batch_data.get("articles", [])
                
                significance_scores.append(significance)
                all_significant_articles.extend(articles)
        
        # Calculate average significance across all batches
        avg_significance = sum(significance_scores) / len(significance_scores) if significance_scores else 0.0
        
        logger.info(f"Completed {len(batch_results)} batches for {ticker} company-specific: avg significance = {avg_significance:.3f}, {len(all_significant_articles)} significant articles")
        
        return {
            ticker: {
                "significance": avg_significance,
                "articles": all_significant_articles
            }
        }
        
    except Exception as e:
        logger.error(f"Error in company-specific analysis for {ticker}: {e}")
        return {
            ticker: {
                "significance": 0.0,
                "articles": [],
                "error": str(e)
            }
        }


async def analyze_all_comparisons(
    ticker: str,
    ticker_news: List[Dict[str, Any]],
    ticker_price: Dict[str, Any],
    comparison_tickers: List[str],
    comparison_news: Dict[str, List[Dict[str, Any]]],
    comparison_prices: Dict[str, Dict[str, Any]],
    model: str = "gpt-5-nano"
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze the main ticker against all comparison tickers (indices + peers) in parallel
    
    Args:
        ticker: The primary ticker being analyzed
        ticker_news: News for the main ticker
        ticker_price: Price for the main ticker
        comparison_tickers: List of all comparison tickers (indices + peers)
        comparison_news: News for all comparison tickers
        comparison_prices: Prices for all comparison tickers
        model: OpenAI model to use for analysis
        
    Returns:
        Dictionary with all comparison results:
        {
            "comparison_ticker_1": {
                "significance": 0.0-1.0,
                "articles": [...]
            },
            "comparison_ticker_2": {...},
            ...
        }
    """
    logger.info(f"Analyzing {ticker} against {len(comparison_tickers)} comparison sources in parallel")
    
    # Create comparison tasks
    tasks = []
    valid_comparisons = []
    
    for comp_ticker in comparison_tickers:
        comp_news = comparison_news.get(comp_ticker, [])
        comp_price = comparison_prices.get(comp_ticker, {})
        
        if not comp_price:
            logger.warning(f"No price data for {comp_ticker}, skipping comparison")
            continue
        
        task = analyze_comparison(
            ticker=ticker,
            ticker_news=ticker_news,
            ticker_price=ticker_price,
            comparison_ticker=comp_ticker,
            comparison_news=comp_news,
            comparison_price=comp_price,
            model=model
        )
        tasks.append(task)
        valid_comparisons.append(comp_ticker)
    
    # Execute all comparisons in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine all results into single dictionary
    combined_results = {}
    for comp_ticker, result in zip(valid_comparisons, results):
        if isinstance(result, Exception):
            logger.error(f"Error comparing {ticker} vs {comp_ticker}: {result}")
            combined_results[comp_ticker] = {
                "significance": 0.0,
                "articles": [],
                "error": str(result)
            }
        else:
            # Result is already in format {"comparison_ticker": {"significance": ..., "articles": [...]}}
            combined_results.update(result)
    
    logger.info(f"Completed {len(combined_results)} comparisons for {ticker}")
    return combined_results


async def analyze_significance_node(state: AgentState, model: str = "gpt-5-nano") -> AgentState:
    """
    Analyze significance of collected news using LLM.
    This node expects news_data and price_action_data to already be in state from collect_news_data_node.
    
    Args:
        state: Current agent state with news_data and price_action_data
        model: OpenAI model to use for analysis (default: gpt-5-nano)
        
    Returns:
        Updated agent state with significance analysis
    """
    # Update progress immediately at start
    state["current_step"] = "analyzing_significance"
    state["progress_message"] = "Analyzing news significance with AI"
    
    try:
        ticker = state.get("ticker", "").upper()
        if not ticker:
            state["error"] = "No ticker provided"
            return state
        
        # Get collected data from state
        news_data = state.get("news_data", {})
        price_action_data = state.get("price_action_data", {})
        peers = state.get("peers", [])
        
        if not news_data or not price_action_data:
            state["error"] = "Missing news_data or price_action_data from previous node"
            return state
        
        logger.info(f"Analyzing significance for {ticker} using model: {model}")
        
        # Extract data from state
        ticker_news = news_data.get("ticker", [])
        market_news = news_data.get("market", {})
        peer_news = news_data.get("peers", {})
        
        ticker_price = price_action_data.get("ticker", {})
        market_prices = price_action_data.get("market", {})
        peer_prices = price_action_data.get("peers", {})
        
        # Define market indices
        indices = ["^GSPC", "^DJI", "^IXIC"]
        
        # Prepare comparison lists
        comparison_tickers = indices.copy()
        if peers:
            comparison_tickers.extend(peers)
        
        # Combine all comparison data
        all_comparison_news = {**market_news}
        all_comparison_prices = {**market_prices}
        
        if peers:
            all_comparison_news.update(peer_news)
            all_comparison_prices.update(peer_prices)
        
        # Execute comparison analysis in parallel with company-specific analysis
        logger.info(f"Running comparison analysis and company-specific analysis in parallel")
        
        comparison_task = analyze_all_comparisons(
            ticker=ticker,
            ticker_news=ticker_news,
            ticker_price=ticker_price,
            comparison_tickers=comparison_tickers,
            comparison_news=all_comparison_news,
            comparison_prices=all_comparison_prices,
            model=model
        )
        
        company_task = analyze_company_specific(
            ticker=ticker,
            ticker_news=ticker_news,
            ticker_price=ticker_price,
            model=model
        )
        
        # Execute both analyses in parallel
        comparison_results, company_results = await asyncio.gather(comparison_task, company_task)
        
        # Merge results: company-specific analysis + all comparisons
        all_results = {**comparison_results, **company_results}
        
        # Store results
        state["significance_analysis"] = all_results
        
        # Update metadata
        state["metadata"]["peers_analyzed"] = len(peers)
        state["metadata"]["analysis_completed"] = True
        
        # Calculate total sources analyzed
        total_sources = len(indices) + len(peers) + 1  # indices + peers + ticker
        state["progress_message"] = f"Completed significance analysis for {total_sources} sources"
        logger.info(f"Successfully analyzed significance for {ticker}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in analyze_significance_node: {e}", exc_info=True)
        state["error"] = f"Failed to analyze significance: {str(e)}"
        return state
