import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


def ml_predictor_strategy(data, lookback=5, test_size=0.2):
    """Generate ML-based buy/sell signals using rolling feature windows."""
    if data is None or data.empty:
        return data.copy() if data is not None else pd.DataFrame()

    df = data.copy()
    df['returns_1d'] = df['close'].pct_change()
    df['returns_5d'] = df['close'].pct_change(periods=max(lookback, 5))
    df['volume_change'] = df['volume'].pct_change()
    df['momentum'] = df['close'] - df['close'].shift(lookback)
    df['volatility'] = df['returns_1d'].rolling(window=max(10, lookback), min_periods=1).std()
    df['high_low_ratio'] = df['high'] / df['low']
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

    df = df.dropna().copy()
    if len(df) < 50:
        signals = data.copy()
        signals['signal'] = 0
        signals['position'] = 0
        return signals

    feature_cols = [
        'returns_1d',
        'returns_5d',
        'volume_change',
        'momentum',
        'volatility',
        'high_low_ratio',
    ]
    X = df[feature_cols].to_numpy(dtype=float)
    y = df['target'].to_numpy(dtype=int)

    signals = data.copy()
    signals['signal'] = 0

    min_train_rows = max(30, int(len(df) * (1 - test_size)))
    for i in range(min_train_rows, len(df)):
        train_X = X[:i]
        train_y = y[:i]
        if len(train_X) < 30:
            continue

        scaler = StandardScaler()
        train_X_scaled = scaler.fit_transform(train_X)
        model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        model.fit(train_X_scaled, train_y)

        current_X = X[i:i + 1]
        pred = model.predict(scaler.transform(current_X))[0]
        if df.index[i] in signals.index:
            signals.loc[df.index[i], 'signal'] = int(pred)

    signals['position'] = signals['signal'].diff().fillna(0)
    return signals