"""
Test script for analyze_news_significance_node functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.nodes.analyze_news_significance_node import collect_news_node
from app.agents.nodes.analysis_summary_node import generate_summary_node
from app.agents.state import AgentState


def print_articles(articles, title, max_display=5):
    """Helper function to print article details"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    
    if not articles:
        print("  No articles found")
        return
    
    print(f"Total articles: {len(articles)}")
    
    for i, article in enumerate(articles[:max_display], 1):
        print(f"\n{i}. {article.get('title', 'No title')}")
        print(f"   Publisher: {article.get('publisher', 'N/A')}")
        print(f"   URL: {article.get('url', 'N/A')[:80]}...")
        print(f"   Published: {article.get('published_time', 'N/A')}")
        
        # Show article text preview if available
        article_text = article.get('text', '')
        if article_text:
            preview = article_text[:150] + "..." if len(article_text) > 150 else article_text
            print(f"   Text Preview: {preview}")
        else:
            summary = article.get('summary', '')
            if summary:
                preview = summary[:150] + "..." if len(summary) > 150 else summary
                print(f"   Summary: {preview}")
    
    if len(articles) > max_display:
        print(f"\n   ... and {len(articles) - max_display} more articles")


async def test_full_node():
    """Test the complete collect_news_node and display all articles"""
    print("\n" + "="*80)
    print("TESTING ANALYZE NEWS SIGNIFICANCE NODE")
    print("="*80)
    
    ticker = "AFRM"
    
    # Initialize state
    state = AgentState()
    state["ticker"] = ticker
    state["messages"] = []
    state["metadata"] = {}
    state["query"] = f"Analyze {ticker} price movement"
    
    print(f"\nTicker: {ticker}")
    print("Running full analysis (fetching peers, news, prices, and analyzing significance)...")
    
    # Run the full node
    result_state = await collect_news_node(state, model="gpt-4o")
    
    # Check for errors
    if "error" in result_state and result_state.get("error"):
        print(f"\n❌ Error: {result_state['error']}")
        return result_state
    
    print(f"\n✓ Analysis complete!")
    
    # ============================================================================
    # RUN SUMMARY NODE
    # ============================================================================
    print("\n" + "="*80)
    print("RUNNING SUMMARY NODE")
    print("="*80)
    print("\nGenerating summary of significant articles...")
    
    result_state = await generate_summary_node(result_state, model="gpt-4o")
    
    if "error" in result_state and result_state.get("error"):
        print(f"\n❌ Summary Error: {result_state['error']}")
    else:
        print(f"✓ Summary generated!")
    
    # ============================================================================
    # DISPLAY PEERS
    # ============================================================================
    peers = result_state.get('peers', [])
    print(f"\n{'='*80}")
    print(f"PEERS DISCOVERED")
    print(f"{'='*80}")
    if peers:
        print(f"Found {len(peers)} peer companies: {', '.join(peers)}")
    else:
        print("No peers found")
    
    # ============================================================================
    # DISPLAY PRICE ACTION
    # ============================================================================
    price_data = result_state.get('price_action_data', {})
    print(f"\n{'='*80}")
    print(f"PRICE ACTION DATA")
    print(f"{'='*80}")
    
    ticker_price = price_data.get('ticker', {})
    if ticker_price:
        change = ticker_price.get('regular_market_change_percent', 0)
        print(f"\n{ticker}:")
        print(f"  Price: ${ticker_price.get('regular_market_price', 'N/A')}")
        print(f"  Change: {change:.2f}%")
        print(f"  Volume: {ticker_price.get('regular_market_volume', 'N/A')}")
    
    market_prices = price_data.get('market', {})
    if market_prices:
        print(f"\nMarket Indices:")
        for idx, price_info in market_prices.items():
            if price_info:
                change = price_info.get('regular_market_change_percent', 0)
                print(f"  {idx}: ${price_info.get('regular_market_price', 'N/A')} ({change:.2f}%)")
    
    # ============================================================================
    # DISPLAY ALL ARTICLES BY SOURCE
    # ============================================================================
    news_data = result_state.get('news_data', {})
    
    # Display ticker news
    ticker_news = news_data.get('ticker', [])
    print_articles(ticker_news, f"TICKER NEWS: {ticker} ({len(ticker_news)} articles)", max_display=10)
    
    # Display market index news
    market_news = news_data.get('market', {})
    for idx, articles in market_news.items():
        print_articles(articles, f"INDEX NEWS: {idx} ({len(articles)} articles)", max_display=5)
    
    # Display peer news
    peer_news = news_data.get('peers', {})
    for peer, articles in peer_news.items():
        print_articles(articles, f"PEER NEWS: {peer} ({len(articles)} articles)", max_display=5)
    
    # ============================================================================
    # DISPLAY SIGNIFICANCE ANALYSIS
    # ============================================================================
    significance_analysis = result_state.get('significance_analysis', {})
    print(f"\n{'='*80}")
    print(f"SIGNIFICANCE ANALYSIS RESULTS")
    print(f"{'='*80}")
    
    if significance_analysis:
        print(f"\nAnalyzed {len(significance_analysis)} sources:\n")
        
        # Sort by significance score
        sorted_analysis = sorted(
            significance_analysis.items(),
            key=lambda x: x[1].get('significance', 0) if isinstance(x[1], dict) else 0,
            reverse=True
        )
        
        for source, data in sorted_analysis:
            if isinstance(data, dict) and 'significance' in data:
                significance = data.get('significance', 0)
                relevant_articles = data.get('articles', [])
                
                print(f"{source}:")
                print(f"  Significance Score: {significance:.3f}")
                print(f"  Relevant Articles: {len(relevant_articles)}")
                
                if relevant_articles:
                    print(f"\n  Articles with Full Text:")
                    for i, article in enumerate(relevant_articles, 1):
                        print(f"\n  {i}. {article.get('title', 'No title')}")
                        print(f"     URL: {article.get('url', 'N/A')}")
                        print(f"     Publisher: {article.get('publisher', 'N/A')}")
                        print(f"     Published: {article.get('published_time', 'N/A')}")
                        
                        # Display full article text
                        article_text = article.get('text', '')
                        if article_text:
                            print(f"\n     ARTICLE TEXT:")
                            print(f"     {'-'*70}")
                            # Indent the text for better readability
                            text_lines = article_text.split('\n')
                            for line in text_lines[:50]:  # Limit to 50 lines per article
                                print(f"     {line}")
                            if len(text_lines) > 50:
                                print(f"     ... ({len(text_lines) - 50} more lines)")
                            print(f"     {'-'*70}")
                        else:
                            summary = article.get('summary', 'No text or summary available')
                            print(f"\n     SUMMARY:")
                            print(f"     {summary}")
                
                print()
    else:
        print("\n⚠️ No significance analysis results")
    
    # ============================================================================
    # DISPLAY NEWS SUMMARY
    # ============================================================================
    news_summary = result_state.get('news_summary', '')
    print(f"\n{'='*80}")
    print(f"NEWS SUMMARY")
    print(f"{'='*80}")
    
    if news_summary:
        print(f"\n{news_summary}\n")
        
        # Show summary stats
        metadata = result_state.get('metadata', {})
        sig_articles_count = metadata.get('significant_articles_count', 0)
        print(f"\nSummary Stats:")
        print(f"  Significant articles (>0.5): {sig_articles_count}")
        print(f"  Summary generated: {metadata.get('summary_generated', False)}")
    else:
        print("\n⚠️ No summary generated")
    
    return result_state


async def main():
    """Run the complete news significance node test"""
    try:
        await test_full_node()
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
