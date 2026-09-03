import pandas as pd


def moving_average_strategy(data, short_window=20, long_window=50):
    # simple MA crossover
    s = data.copy()
    s["short_ma"] = s["close"].rolling(window=short_window, min_periods=1).mean()
    s["long_ma"] = s["close"].rolling(window=long_window, min_periods=1).mean()
    s["signal"] = 0
    s.loc[s["short_ma"] > s["long_ma"], "signal"] = 1
    s.loc[s["short_ma"] <= s["long_ma"], "signal"] = 0
    # position is when the signal changes (for plotting/analysis)
    s["position"] = s["signal"].diff()
    return s
