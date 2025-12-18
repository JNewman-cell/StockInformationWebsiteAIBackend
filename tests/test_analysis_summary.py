"""
Test script for analysis_summary_node
"""

import asyncio
import logging
from app.agents.state import AgentState
from app.agents.nodes.analysis_summary_node import generate_summary_node, filter_significant_articles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_filter_significant_articles():
    """Test filtering of significant articles"""
    logger.info("=" * 80)
    logger.info("TEST: Filter Significant Articles")
    logger.info("=" * 80)
    
    # Mock significance analysis data
    mock_analysis = {
        "AAPL": {
            "significance": 0.75,
            "articles": [
                {
                    "title": "Apple announces record Q4 earnings",
                    "summary": "Apple Inc. reported record quarterly earnings...",
                    "published": "2024-01-15"
                },
                {
                    "title": "New iPhone features revealed",
                    "summary": "Apple showcases innovative features...",
                    "published": "2024-01-14"
                }
            ]
        },
        "^GSPC": {
            "significance": 0.62,
            "articles": [
                {
                    "title": "S&P 500 reaches new high",
                    "summary": "Market indices surge on strong economic data...",
                    "published": "2024-01-15"
                }
            ]
        },
        "MSFT": {
            "significance": 0.48,  # Below threshold
            "articles": [
                {
                    "title": "Microsoft updates cloud services",
                    "summary": "Minor cloud infrastructure updates...",
                    "published": "2024-01-14"
                }
            ]
        },
        "NVDA": {
            "significance": 0.55,
            "articles": [
                {
                    "title": "NVIDIA announces new AI chip",
                    "summary": "Revolutionary AI processing capabilities...",
                    "published": "2024-01-15"
                }
            ]
        }
    }
    
    filtered = filter_significant_articles(mock_analysis, threshold=0.5)
    
    logger.info(f"\nTotal sources analyzed: {len(mock_analysis)}")
    logger.info(f"Sources above threshold (0.5): {sum(1 for v in mock_analysis.values() if isinstance(v, dict) and v.get('significance', 0) >= 0.5)}")
    logger.info(f"Total significant articles: {len(filtered)}")
    
    logger.info("\nSignificant articles:")
    for article in filtered:
        logger.info(f"  - [{article['source']}] {article['title']} (Significance: {article['significance']:.2f})")
    
    assert len(filtered) == 4, f"Expected 4 significant articles, got {len(filtered)}"
    assert filtered[0]["significance"] == 0.75, "Articles should be sorted by significance"
    
    logger.info("\n✅ Filter test passed!")


async def test_generate_summary_full():
    """Test full summary generation with mock data"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Full Summary Generation")
    logger.info("=" * 80)
    
    # Create mock state
    state = AgentState()
    state["ticker"] = "AAPL"
    state["significance_analysis"] = {
        "AAPL": {
            "significance": 0.85,
            "articles": [
                {
                    "title": "Apple Reports Record Q4 2024 Revenue of $120 Billion",
                    "summary": "Apple Inc. announced record-breaking quarterly revenue driven by strong iPhone 15 sales and services growth. The company beat analyst expectations with EPS of $2.10 vs. expected $1.95.",
                    "published": "2024-01-15T14:30:00",
                    "link": "https://example.com/apple-earnings"
                },
                {
                    "title": "Apple Announces Revolutionary Vision Pro 2 Features",
                    "summary": "Apple unveiled significant upgrades to its Vision Pro headset, including improved spatial computing capabilities and lower pricing, potentially expanding the AR/VR market.",
                    "published": "2024-01-14T10:00:00",
                    "link": "https://example.com/vision-pro"
                }
            ]
        },
        "^GSPC": {
            "significance": 0.65,
            "articles": [
                {
                    "title": "S&P 500 Hits All-Time High on Tech Rally",
                    "summary": "Major indices surge as technology stocks lead broad market gains. S&P 500 closes above 5,000 for the first time, driven by optimism about economic soft landing.",
                    "published": "2024-01-15T16:00:00",
                    "link": "https://example.com/sp500-high"
                }
            ]
        },
        "^DJI": {
            "significance": 0.45,  # Below threshold
            "articles": [
                {
                    "title": "Dow Jones Posts Modest Gains",
                    "summary": "Industrial average edges higher in quiet trading session.",
                    "published": "2024-01-15T16:00:00",
                    "link": "https://example.com/dow"
                }
            ]
        },
        "NVDA": {
            "significance": 0.72,
            "articles": [
                {
                    "title": "NVIDIA's Latest AI Chip Breaks Performance Records",
                    "summary": "NVIDIA announced the H200 GPU with unprecedented AI training capabilities, solidifying its dominance in the AI infrastructure market. Stock surges 8% on the news.",
                    "published": "2024-01-14T09:00:00",
                    "link": "https://example.com/nvidia-h200"
                }
            ]
        },
        "GOOGL": {
            "significance": 0.58,
            "articles": [
                {
                    "title": "Google Announces Breakthrough in Quantum Computing",
                    "summary": "Alphabet's quantum computing division demonstrates error correction breakthrough, bringing practical quantum computers closer to reality.",
                    "published": "2024-01-13T11:00:00",
                    "link": "https://example.com/google-quantum"
                }
            ]
        }
    }
    
    # Generate summary
    result_state = await generate_summary_node(state, model="gpt-4o-mini")
    
    logger.info(f"\nTicker: {result_state['ticker']}")
    logger.info(f"Significant articles found: {result_state['metadata'].get('significant_articles_count', 0)}")
    logger.info(f"Summary generated: {result_state['metadata'].get('summary_generated', False)}")
    
    logger.info("\n" + "=" * 80)
    logger.info("GENERATED SUMMARY:")
    logger.info("=" * 80)
    logger.info(result_state.get("news_summary", "No summary generated"))
    logger.info("=" * 80)
    
    assert result_state.get("news_summary"), "Summary should be generated"
    assert result_state["metadata"].get("significant_articles_count", 0) == 5, "Should have 5 significant articles"
    
    logger.info("\n✅ Full summary generation test passed!")


async def test_no_significant_articles():
    """Test behavior when no articles meet threshold"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: No Significant Articles")
    logger.info("=" * 80)
    
    state = AgentState()
    state["ticker"] = "TEST"
    state["significance_analysis"] = {
        "TEST": {
            "significance": 0.30,
            "articles": [{"title": "Minor news", "summary": "Not significant"}]
        },
        "^GSPC": {
            "significance": 0.25,
            "articles": [{"title": "Market update", "summary": "Routine update"}]
        }
    }
    
    result_state = await generate_summary_node(state)
    
    logger.info(f"\nSummary: {result_state.get('news_summary')}")
    
    assert "No news articles were found to have significant relevance" in result_state.get("news_summary", "")
    
    logger.info("\n✅ No significant articles test passed!")


async def test_empty_analysis():
    """Test behavior with empty significance analysis"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Empty Analysis")
    logger.info("=" * 80)
    
    state = AgentState()
    state["ticker"] = "TEST"
    state["significance_analysis"] = {}
    
    result_state = await generate_summary_node(state)
    
    logger.info(f"\nSummary: {result_state.get('news_summary')}")
    
    assert result_state.get("news_summary") == "No news analysis available."
    
    logger.info("\n✅ Empty analysis test passed!")


async def main():
    """Run all tests"""
    try:
        await test_filter_significant_articles()
        await test_no_significant_articles()
        await test_empty_analysis()
        await test_generate_summary_full()
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
