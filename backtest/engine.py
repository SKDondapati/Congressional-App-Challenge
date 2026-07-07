import pandas as pd
import numpy as np

def run_simulation(data, signals, starting_money=10000):
    df = signals.copy()
    df['daily_return'] = data['close'].pct_change().fillna(0)
    df['strategy_return'] = df['signal'].shift(1).fillna(0) * df['daily_return']
    df['portfolio_value'] = (1 + df['strategy_return']).cumprod() * starting_money
    df['buy_hold_value'] = (1 + df['daily_return']).cumprod() * starting_money
    return df


def calculate_stats(results, risk_free_rate=0.0):
    if results is None or results.empty:
        return {
            'final_value': 0.0,
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
        }

    final_value = results['portfolio_value'].iloc[-1]
    start_value = results['portfolio_value'].iloc[0]
    total_return = final_value / start_value - 1 if start_value != 0 else 0.0

    returns = results['strategy_return'].fillna(0)
    if len(returns) < 2 or returns.std(ddof=1) == 0:
        sharpe_ratio = 0.0
    else:
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std(ddof=1)

    cum_max = results['portfolio_value'].cummax()
    drawdown = (results['portfolio_value'] - cum_max) / cum_max
    max_drawdown = drawdown.min() if not drawdown.empty else 0.0

    return {
        'final_value': float(final_value),
        'total_return': float(total_return),
        'sharpe_ratio': float(sharpe_ratio),
        'max_drawdown': float(max_drawdown),
    }
