import pandas as pd
import numpy as np

def run_simulation(data, signals, starting_money=10000):
    df = signals.copy()
    df['daily_return'] = data['close'].pct_change()
    df['strategy_return'] = df['signal'].shift(1) * df['daily_return']
    df['portfolio_value'] = (1 + df['strategy_return']).cumprod() * starting_money
    df['buy_hold_value'] = (1 + df['daily_return']).cumprod() * starting_money
    return df
