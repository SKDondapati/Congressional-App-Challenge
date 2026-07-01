import yfinance as yf

def download_market_data(ticker, start_date, end_date):
    try:
        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            print("No data found for that ticker.")
            return df
        return df
    except:
        print("Something went wrong downloading data.")
        return None

def clean_price_data(raw_df):
    if raw_df is None or raw_df.empty:
        return raw_df
    df = raw_df.copy()
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df = df.dropna()
    return df
