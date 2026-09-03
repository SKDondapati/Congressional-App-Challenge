import numpy as np
import pandas as pd


def run_simulation(data, signals, starting_money=10000):
    # simple sim: multiply daily returns under the strategy
    df = signals.copy()
    df["daily_return"] = data["close"].pct_change().fillna(0)
    # we use yesterday's signal to decide today's return
    df["strategy_return"] = df["signal"].shift(1).fillna(0) * df["daily_return"]
    df["portfolio_value"] = (1 + df["strategy_return"]).cumprod() * starting_money
    df["buy_hold_value"] = (1 + df["daily_return"]).cumprod() * starting_money
    return df


def calculate_stats(results, risk_free_rate=0.0):
    # return some basic stats; keep it dumb and understandable
    if results is None or results.empty:
        return {
            "final_value": 0.0,
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
        }

    fv = results["portfolio_value"].iloc[-1]
    sv = results["portfolio_value"].iloc[0]
    tr = fv / sv - 1 if sv != 0 else 0.0

    rets = results["strategy_return"].fillna(0)
    if len(rets) < 2 or rets.std(ddof=1) == 0:
        sr = 0.0
    else:
        # simple annualized sharpe using 252 trading days
        excess = rets - risk_free_rate / 252
        sr = np.sqrt(252) * excess.mean() / excess.std(ddof=1)

    cm = results["portfolio_value"].cummax()
    dd = (results["portfolio_value"] - cm) / cm
    md = dd.min() if not dd.empty else 0.0

    return {
        "final_value": float(fv),
        "total_return": float(tr),
        "sharpe_ratio": float(sr),
        "max_drawdown": float(md),
    }
