import numpy as np
import pandas as pd


def run_simulation(data, signals, starting_money=10000, monthly_contribution=0):
    # Simulate portfolio over time with optional monthly contributions.
    # We iterate day-by-day and add contributions at the START of the first
    # trading day of each month (before applying that day's return). This
    # models contributions being invested immediately at the month's opening
    # trading day.
    df = signals.copy()
    df = df.reindex(data.index).copy()
    daily_returns = data["close"].pct_change().fillna(0)

    dates = list(df.index)
    n = len(dates)
    portfolio_vals = []
    buy_hold_vals = []
    strat_rets = []

    value = float(starting_money)
    bh_value = float(starting_money)

    prev_month = dates[0].month if n > 0 else None

    for i in range(n):
        date = dates[i]
        dr = float(daily_returns.iloc[i]) if i < len(daily_returns) else 0.0

        # Decide today's position using yesterday's signal (keep previous behavior)
        sig = 0.0
        if i - 1 >= 0:
            try:
                sig = float(df["signal"].iloc[i - 1])
            except Exception:
                sig = 0.0


        # Add monthly contribution on the first trading day of a new month (start of month)
        if date.month != prev_month and i != 0:
            value += float(monthly_contribution)
            bh_value += float(monthly_contribution)
            prev_month = date.month

        strat_ret = sig * dr
        value = value * (1 + strat_ret)
        bh_value = bh_value * (1 + dr)

        portfolio_vals.append(value)
        buy_hold_vals.append(bh_value)
        strat_rets.append(strat_ret)

    df["daily_return"] = daily_returns
    df["strategy_return"] = pd.Series(strat_rets, index=df.index)
    df["portfolio_value"] = pd.Series(portfolio_vals, index=df.index)
    df["buy_hold_value"] = pd.Series(buy_hold_vals, index=df.index)

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
