import pandas as pd

def moving_average_strategy(data, short_window=20, long_window=50):
    signals = data.copy()
    signals['short_ma'] = signals['close'].rolling(window=short_window, min_periods=1).mean()
    signals['long_ma'] = signals['close'].rolling(window=long_window, min_periods=1).mean()
    signals['signal'] = 0
    signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
    signals.loc[signals['short_ma'] <= signals['long_ma'], 'signal'] = 0
    signals['position'] = signals['signal'].diff()
    return signals