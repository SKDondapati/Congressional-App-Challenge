def buy_hold_strategy(data):
    signals = data.copy()
    signals['signal'] = 1
    signals['position'] = 0
    signals.loc[signals.index[0], 'position'] = 1
    return signals
