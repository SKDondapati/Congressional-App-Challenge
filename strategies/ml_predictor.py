import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


def ml_predictor_strategy(data, lookback=5, test_size=0.2):
    # a quick ML-based signal generator using previous windows
    if data is None or data.empty:
        return data.copy() if data is not None else pd.DataFrame()

    d = data.copy()
    d["returns_1d"] = d["close"].pct_change()
    d["returns_5d"] = d["close"].pct_change(periods=max(lookback, 5))
    d["volume_change"] = d["volume"].pct_change()
    d["momentum"] = d["close"] - d["close"].shift(lookback)
    d["volatility"] = (
        d["returns_1d"].rolling(window=max(10, lookback), min_periods=1).std()
    )
    d["high_low_ratio"] = d["high"] / d["low"]
    d["target"] = (d["close"].shift(-1) > d["close"]).astype(int)

    d = d.dropna().copy()
    if len(d) < 50:
        s = data.copy()
        s["signal"] = 0
        s["position"] = 0
        return s

    cols = [
        "returns_1d",
        "returns_5d",
        "volume_change",
        "momentum",
        "volatility",
        "high_low_ratio",
    ]
    X = d[cols].to_numpy(dtype=float)
    y = d["target"].to_numpy(dtype=int)

    s = data.copy()
    s["signal"] = 0

    min_train_rows = max(30, int(len(d) * (1 - test_size)))
    for i in range(min_train_rows, len(d)):
        train_X = X[:i]
        train_y = y[:i]
        if len(train_X) < 30:
            continue

        scaler = StandardScaler()
        tX = scaler.fit_transform(train_X)
        model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        model.fit(tX, train_y)

        curX = X[i : i + 1]
        pred = model.predict(scaler.transform(curX))[0]
        if d.index[i] in s.index:
            s.loc[d.index[i], "signal"] = int(pred)

    s["position"] = s["signal"].diff().fillna(0)
    return s
