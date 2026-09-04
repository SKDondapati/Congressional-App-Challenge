import pandas as pd
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
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.columns = ["open", "high", "low", "close", "volume"]
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
        tickers = [t.strip() for t in tickers.split(",") if t.strip()]

    # get each ticker and tag its columns so we can combine later
    dfs = []
    for t in tickers:
        raw = download_market_data(t, start_date, end_date)
        if raw is None or raw.empty:
            continue
        d = clean_price_data(raw)
        d = d[["open", "high", "low", "close", "volume"]].copy()
        d.columns = pd.MultiIndex.from_product([[t], d.columns])
        dfs.append(d)

    if not dfs:
        return None

    # Concatenate on columns, align on index
    combined = pd.concat(dfs, axis=1)

    # Build an equal-weight portfolio using returns (not raw price averaging).
    # Compute per-asset close returns, average those returns to get portfolio
    # returns, then compound to a price series. This avoids bias from different
    # share prices (e.g., AAPL vs BRK.A). Volume remains summed.
    close_cols = [c for c in combined.columns if c[1] == "close"]
    close_df = combined[close_cols].copy()

    # pct_change will produce NaN for the first row; compute returns and drop NaNs
    returns = close_df.pct_change()
    returns = returns.dropna(how="all")

    if returns.empty:
        # fallback to simple mean if returns can't be computed
        close_series = close_df.mean(axis=1)
    else:
        # portfolio returns: equal-weight average of asset returns
        portfolio_returns = returns.mean(axis=1)

        # use the mean of the first available closes as a sensible starting value
        first_closes = close_df.iloc[0].mean()

        # compound returns to get portfolio close prices; align index to include first date
        compounded = (1 + portfolio_returns).cumprod()
        compounded.index = portfolio_returns.index
        # prepend the initial value at the first close date
        first_date = close_df.index[0]
        close_series = pd.Series([first_closes], index=[first_date]).append(
            first_closes * compounded
        )

    # For simplicity and consistency, set OHLC to the portfolio close series.
    open_avg = close_series.copy()
    high_avg = close_series.copy()
    low_avg = close_series.copy()

    vol_cols = [c for c in combined.columns if c[1] == "volume"]
    vol_sum = combined[vol_cols].sum(axis=1)

    out = pd.DataFrame(
        {
            "open": open_avg,
            "high": high_avg,
            "low": low_avg,
            "close": close_series,
            "volume": vol_sum,
        }
    )

    out = out.dropna()
    return out
