import logging

import pandas as pd
import yfinance as yf


logger = logging.getLogger(__name__)


class MarketDataError(ValueError):
    """An input or market-data request could not be used."""


def _validate_request(ticker, start_date, end_date):
    if not isinstance(ticker, str) or not ticker.strip():
        raise MarketDataError("Enter at least one ticker symbol.")

    start = pd.to_datetime(start_date, errors="coerce")
    end = pd.to_datetime(end_date, errors="coerce")
    if pd.isna(start) or pd.isna(end):
        raise MarketDataError("Enter valid start and end dates.")
    if start > end:
        raise MarketDataError("Start date must be on or before end date.")


def download_market_data(ticker, start_date, end_date):
    _validate_request(ticker, start_date, end_date)
    try:
        data = yf.download(
            ticker.strip(), start=start_date, end=end_date, progress=False
        )
        if data is None or data.empty:
            raise MarketDataError(
                f"No market data was returned for {ticker.strip()}. Check the symbol and dates."
            )
        return data
    except MarketDataError:
        raise
    except Exception as error:
        logger.exception("Market data download failed for %s", ticker)
        raise MarketDataError(
            f"Could not download {ticker.strip()}. Check the symbol and your internet connection."
        ) from error


def clean_price_data(raw_df):
    if raw_df is None or raw_df.empty:
        raise MarketDataError("The data source returned no price data.")
    df = raw_df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        price_names = {"open", "high", "low", "close", "volume"}
        selected = {}
        for column in df.columns:
            for part in column:
                name = str(part).lower()
                if name in price_names and name not in selected:
                    selected[name] = column
        df = df[[selected[name] for name in selected]].copy()
        df.columns = list(selected)
    else:
        df.columns = [str(column).lower() for column in df.columns]

    if "close" not in df.columns:
        raise MarketDataError("The downloaded data does not include closing prices.")

    df = df.loc[~df.index.duplicated(keep="last")].sort_index()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"])
    df = df[(df["close"] > 0) & (df["close"] < float("inf"))]
    if df.empty:
        raise MarketDataError("No valid closing prices were returned.")

    for name in ["open", "high", "low", "volume"]:
        if name not in df.columns:
            df[name] = df["close"] if name != "volume" else 0.0
        else:
            df[name] = pd.to_numeric(df[name], errors="coerce")
    return df[["open", "high", "low", "close", "volume"]]


def download_market_data_multi(tickers, start_date, end_date):
    """Download multiple tickers and return an equal-weight aggregated price series.

    Returns a DataFrame with columns ['open','high','low','close','volume'] where
    'close' is the equal-weight average of component closes and other fields are aggregated.
    """
    if isinstance(tickers, str):
        tickers = [t.strip() for t in tickers.split(",") if t.strip()]
    if not tickers:
        raise MarketDataError("Enter at least one ticker symbol.")

    # get each ticker and tag its columns so we can combine later
    dfs = []
    for t in tickers:
        try:
            raw = download_market_data(t, start_date, end_date)
        except MarketDataError as error:
            logger.warning("Skipping %s: %s", t, error)
            continue
        if raw is None or raw.empty:
            continue
        try:
            d = clean_price_data(raw)
        except MarketDataError:
            logger.warning("Skipping %s because it has no usable prices", t)
            continue
        d = d[["open", "high", "low", "close", "volume"]].copy()
        d.columns = pd.MultiIndex.from_product([[t], d.columns])
        dfs.append(d)

    if not dfs:
        raise MarketDataError("No usable data was found for the selected tickers.")

    # Concatenate on columns, align on index
    combined = pd.concat(dfs, axis=1)

    # Build an equal-weight portfolio using returns (not raw price averaging).
    # Compute per-asset close returns, average those returns to get portfolio
    # returns, then compound to a price series. This avoids bias from different
    # share prices (e.g., AAPL vs BRK.A). Volume remains summed.
    close_cols = [c for c in combined.columns if c[1] == "close"]
    close_df = combined[close_cols].copy()

    # pct_change will produce NaN for the first row; compute returns and drop NaNs
    returns = close_df.pct_change(fill_method=None)
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
        later_closes = first_closes * compounded
        later_closes = later_closes.loc[later_closes.index != first_date]
        close_series = pd.concat(
            [pd.Series([first_closes], index=[first_date]), later_closes]
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
