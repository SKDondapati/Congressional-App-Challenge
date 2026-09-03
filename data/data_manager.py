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


def download_market_data_multi(tickers, start_date, end_date):
    """Download multiple tickers and return an equal-weight aggregated price series.

    Returns a DataFrame with columns ['open','high','low','close','volume'] where
    'close' is the equal-weight average of component closes and other fields are aggregated.
    """
    if not tickers:
        return None
    if isinstance(tickers, str):
        tickers = [t.strip() for t in tickers.split(',') if t.strip()]

    dfs = []
    for t in tickers:
        raw = download_market_data(t, start_date, end_date)
        if raw is None or raw.empty:
            continue
        df = clean_price_data(raw)
        df = df[['open', 'high', 'low', 'close', 'volume']].copy()
        df.columns = pd.MultiIndex.from_product([[t], df.columns])
        dfs.append(df)

    if not dfs:
        return None

    # Concatenate on columns, align on index
    combined = pd.concat(dfs, axis=1)

    # Compute equal-weight close average
    close_cols = [c for c in combined.columns if c[1] == 'close']
    close_df = combined[close_cols]
    # average across tickers
    close_avg = close_df.mean(axis=1)

    # For open/high/low take mean of components; volume summed
    open_cols = [c for c in combined.columns if c[1] == 'open']
    high_cols = [c for c in combined.columns if c[1] == 'high']
    low_cols = [c for c in combined.columns if c[1] == 'low']
    vol_cols = [c for c in combined.columns if c[1] == 'volume']

    open_avg = combined[open_cols].mean(axis=1)
    high_avg = combined[high_cols].mean(axis=1)
    low_avg = combined[low_cols].mean(axis=1)
    vol_sum = combined[vol_cols].sum(axis=1)

    out = pd.DataFrame({
        'open': open_avg,
        'high': high_avg,
        'low': low_avg,
        'close': close_avg,
        'volume': vol_sum,
    })

    out = out.dropna()
    return out
