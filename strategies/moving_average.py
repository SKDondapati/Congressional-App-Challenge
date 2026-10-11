import pandas as pd


def moving_average_strategy(data, short_window=20, long_window=50):
    """Go long after both averages exist and the short average is higher."""
    if short_window < 1 or long_window < 1:
        raise ValueError("Moving-average windows must be positive.")
    if long_window <= short_window:
        raise ValueError("The long window must be greater than the short window.")

    s = data.copy()
    if "close" not in s.columns:
        raise ValueError("Price data must include a 'close' column.")
    s["short_ma"] = s["close"].rolling(
        window=short_window, min_periods=short_window
    ).mean()
    s["long_ma"] = s["close"].rolling(
        window=long_window, min_periods=long_window
    ).mean()
    s["signal"] = (s["short_ma"] > s["long_ma"]).astype(int)
    # position is when the signal changes (for plotting/analysis)
    s["position"] = s["signal"].diff()
    return s
