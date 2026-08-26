import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def ml_predictor_strategy(data, lookback=5, test_size=0.2):
    """
    Generates trading signals using a Random Forest classifier.
    Predicts if price will go up tomorrow based on past returns and volatility.
    """
    df = data.copy()
    
    # Create features
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(5).std()
    df['momentum'] = df['close'] - df['close'].shift(lookback)
    
    # Create target (1 if price goes up tomorrow, 0 if down)
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    
    # Drop NaN values
    df = df.dropna()
    
    # If not enough data, return all zeros
    if len(df) < 30:
        signals = data.copy()
        signals['signal'] = 0
        signals['position'] = 0
        return signals
    
    # Features and target
    feature_cols = ['returns', 'volatility', 'momentum']
    X = df[feature_cols].values
    y = df['target'].values
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split into train and test
    split_idx = int(len(X_scaled) * (1 - test_size))
    X_train = X_scaled[:split_idx]
    X_test = X_scaled[split_idx:]
    y_train = y[:split_idx]
    y_test = y[split_idx:]
    
    # Train model
    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    # Make predictions on all data (or just test)
    predictions = model.predict(X_scaled)
    
    # Create signals DataFrame aligned with original data
    signals = data.loc[df.index].copy()
    signals['signal'] = predictions
    signals['position'] = signals['signal'].diff()
    
    return signals