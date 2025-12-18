"""Quick test of yahooquery library"""
from yahooquery import Ticker

# Test news fetching
print("Testing yahooquery news fetch...")
ticker = Ticker("AAPL")
news = ticker.news(count=5)

print(f"Type of news: {type(news)}")
print(f"News data: {news}")

if isinstance(news, dict):
    print("\nNews is a dictionary with keys:", news.keys())
    for key, value in news.items():
        print(f"  {key}: {type(value)}")
        if isinstance(value, list):
            print(f"    Length: {len(value)}")
            if len(value) > 0:
                print(f"    First item type: {type(value[0])}")
                print(f"    First item keys: {value[0].keys() if isinstance(value[0], dict) else 'N/A'}")

# Test quotes fetching
print("\n\nTesting yahooquery quotes fetch...")
quotes = ticker.quotes
print(f"Type of quotes: {type(quotes)}")
print(f"Quotes data: {quotes}")
