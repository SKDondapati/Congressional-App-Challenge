import numpy as np
import pandas as pd


def run_simulation(
    data,
    signals,
    starting_money=10000,
    monthly_contribution=0,
    start_date=None,
):
    """Simulate long-only signals; a signal is applied to the next day's return.

    Contributions are added before returns on the first trading day of each
    month after the simulation starts. ``start_date`` lets strategies share an
    evaluation window while still using the prior close to calculate returns.
    """
    if starting_money < 0 or monthly_contribution < 0:
        raise ValueError("Starting money and monthly contributions cannot be negative.")

    if data is None or data.empty:
        return pd.DataFrame(
            columns=[
                "daily_return",
                "strategy_return",
                "contribution",
                "performance_index",
                "portfolio_value",
                "buy_hold_value",
            ]
        )
    if "close" not in data.columns:
        raise ValueError("Price data must include a 'close' column.")

    prices = pd.to_numeric(data["close"], errors="coerce")
    valid = prices.notna() & np.isfinite(prices) & (prices > 0)
    prices = prices.loc[valid]
    prices = prices.loc[~prices.index.duplicated(keep="last")].sort_index()
    if prices.empty:
        raise ValueError("Price data must include at least one positive closing price.")

    aligned_signals = signals.reindex(prices.index)
    if "signal" not in aligned_signals.columns:
        aligned_signals["signal"] = 0.0
    positions = pd.to_numeric(aligned_signals["signal"], errors="coerce")
    positions = positions.fillna(0.0).shift(1).fillna(0.0)

    all_returns = prices.pct_change(fill_method=None).fillna(0.0)
    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        selected_dates = prices.index[prices.index >= start_date]
    else:
        selected_dates = prices.index

    if len(selected_dates) == 0:
        return pd.DataFrame(index=selected_dates)

    results = pd.DataFrame(index=selected_dates)
    results["daily_return"] = all_returns.reindex(selected_dates).fillna(0.0)
    results["strategy_return"] = (
        positions.reindex(selected_dates).fillna(0.0)
        * results["daily_return"]
    )

    contributions = []
    previous_month = (selected_dates[0].year, selected_dates[0].month)
    for date in selected_dates:
        current_month = (date.year, date.month)
        contribution = 0.0
        if current_month != previous_month:
            contribution = float(monthly_contribution)
            previous_month = current_month
        contributions.append(contribution)
    results["contribution"] = contributions
    results["total_contributions"] = (
        float(starting_money) + results["contribution"].cumsum()
    )

    portfolio_values = []
    benchmark_values = []
    performance_values = []
    account_value = float(starting_money)
    benchmark_value = float(starting_money)
    performance_value = 1.0

    for date in selected_dates:
        account_value += results.at[date, "contribution"]
        account_value *= 1 + results.at[date, "strategy_return"]
        benchmark_value += results.at[date, "contribution"]
        benchmark_value *= 1 + results.at[date, "daily_return"]
        performance_value *= 1 + results.at[date, "strategy_return"]
        portfolio_values.append(account_value)
        benchmark_values.append(benchmark_value)
        performance_values.append(performance_value)

    results["performance_index"] = performance_values
    results["portfolio_value"] = portfolio_values
    results["buy_hold_value"] = benchmark_values
    return results


def calculate_stats(results, risk_free_rate=0.0):
    """Summarize time-weighted performance (risk-free rate is annualized)."""
    if results is None or results.empty:
        return {
            "final_value": 0.0,
            "total_return": 0.0,
            "total_contributions": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "annualized_volatility": 0.0,
        }

    fv = float(results["portfolio_value"].iloc[-1])
    if "total_contributions" in results:
        total_contributions = float(results["total_contributions"].iloc[-1])
    else:
        total_contributions = 0.0

    rets = results["strategy_return"].fillna(0.0)
    tr = float((1 + rets).prod() - 1)
    if len(rets) < 2 or rets.std(ddof=1) == 0:
        sr = 0.0
    else:
        excess = rets - risk_free_rate / 252
        sr = np.sqrt(252) * excess.mean() / excess.std(ddof=1)

    if "performance_index" in results:
        performance = results["performance_index"]
    else:
        performance = results["portfolio_value"]
    cm = performance.cummax()
    dd = performance.div(cm).sub(1)
    md = dd.min() if not dd.empty else 0.0
    volatility = float(rets.std(ddof=1) * np.sqrt(252)) if len(rets) > 1 else 0.0

    return {
        "final_value": float(fv),
        "total_return": float(tr),
        "total_contributions": total_contributions,
        "sharpe_ratio": float(sr),
        "max_drawdown": float(md),
        "annualized_volatility": volatility,
    }
