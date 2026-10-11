def buy_hold_strategy(data):
    """Stay invested for the full period; a signal of 1 means fully invested."""
    s = data.copy()
    s["signal"] = 1
    s["position"] = 0
    # mark the first day as an entry
    if not s.empty:
        s.loc[s.index[0], "position"] = 1
    return s
