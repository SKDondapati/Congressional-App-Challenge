import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


def ml_predictor_strategy(data, lookback=5, test_size=0.2):
    """Predict next-day direction on a chronological holdout period.

    Signals before the holdout are zero. A prediction is made after that day's
    close and is therefore applied to the following trading day's return.
    """
    if lookback < 1:
        raise ValueError("Lookback must be positive.")
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1.")
    if data is None:
        return pd.DataFrame(columns=["signal", "position", "evaluation_prediction"])

    signals = data.copy()
    signals["signal"] = 0
    signals["evaluation_prediction"] = False
    if signals.empty:
        signals["position"] = 0
        return signals
    if "close" not in signals.columns:
        raise ValueError("Price data must include a 'close' column.")

    close = pd.to_numeric(signals["close"], errors="coerce")
    features = pd.DataFrame(index=signals.index)
    features["returns_1d"] = close.pct_change(fill_method=None)
    features["returns_lookback"] = close.pct_change(
        periods=max(lookback, 5), fill_method=None
    )
    features["momentum"] = close - close.shift(lookback)
    volatility_window = max(10, lookback)
    features["volatility"] = features["returns_1d"].rolling(
        volatility_window, min_periods=volatility_window
    ).std()
    if "volume" in signals.columns:
        volume = pd.to_numeric(signals["volume"], errors="coerce")
        if volume.notna().all() and volume.gt(0).all():
            features["volume_change"] = volume.pct_change(fill_method=None)

    if "high" in signals.columns and "low" in signals.columns:
        high = pd.to_numeric(signals["high"], errors="coerce")
        low = pd.to_numeric(signals["low"], errors="coerce")
        if high.notna().all() and low.notna().all() and high.gt(0).all() and low.gt(0).all():
            features["high_low_ratio"] = high / low
    features = features.replace([np.inf, -np.inf], np.nan).dropna()

    next_close = close.shift(-1)
    labels = next_close.gt(close).where(next_close.notna()).reindex(features.index)
    known_label = labels.notna()
    features = features.loc[known_label]
    labels = labels.loc[known_label].astype(int)
    if len(features) < 50:
        signals["position"] = signals["signal"].diff().fillna(0)
        return signals

    split = max(30, int(len(features) * (1 - test_size)))
    if split >= len(features):
        signals["position"] = signals["signal"].diff().fillna(0)
        return signals

    model = RandomForestClassifier(
        n_estimators=100, max_depth=8, random_state=42, class_weight="balanced"
    )
    model.fit(features.iloc[:split], labels.iloc[:split])
    test_features = features.iloc[split:]
    predictions = model.predict(test_features)
    signals.loc[test_features.index, "signal"] = predictions
    signals.loc[test_features.index, "evaluation_prediction"] = True
    signals["position"] = signals["signal"].diff().fillna(0)
    return signals
