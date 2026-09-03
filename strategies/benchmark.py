def buy_hold_strategy(data):
    # everybody buys and holds
    s = data.copy()
    s["signal"] = 1
    s["position"] = 0
    # mark the first day as an entry
    s.loc[s.index[0], "position"] = 1
    return s
