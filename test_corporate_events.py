from yahooquery import Ticker

if __name__ == "__main__":
    aapl = Ticker('orcl')
    df = aapl.corporate_events
    print(df.head())