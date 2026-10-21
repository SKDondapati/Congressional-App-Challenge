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
    if (
        not np.isfinite(starting_money)
        or not np.isfinite(monthly_contribution)
        or starting_money < 0
        or monthly_contribution < 0
    ):
        raise ValueError("Starting money and monthly contributions must be finite and non-negative.")

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
            "total_return": None,
            "total_contributions": 0.0,
            "annualized_return": None,
            "sharpe_ratio": None,
            "max_drawdown": None,
            "annualized_volatility": None,
        }

    if not np.isfinite(risk_free_rate):
        raise ValueError("Risk-free rate must be finite.")

    portfolio_values = pd.to_numeric(
        results.get("portfolio_value", pd.Series(dtype=float)), errors="coerce"
    )
    portfolio_values = portfolio_values[np.isfinite(portfolio_values)]
    fv = float(portfolio_values.iloc[-1]) if not portfolio_values.empty else 0.0
    if "total_contributions" in results:
        contributions = pd.to_numeric(results["total_contributions"], errors="coerce")
        contributions = contributions[np.isfinite(contributions)]
        total_contributions = float(contributions.iloc[-1]) if not contributions.empty else 0.0
    else:
        total_contributions = 0.0

    rets = pd.to_numeric(
        results.get("strategy_return", pd.Series(dtype=float)), errors="coerce"
    )
    rets = rets[np.isfinite(rets)]
    tr = float((1 + rets).prod() - 1) if not rets.empty else 0.0

    annualized_return = None
    if not rets.empty and tr > -1 and len(results.index) > 1:
        try:
            first_date = pd.Timestamp(results.index[0])
            last_date = pd.Timestamp(results.index[-1])
            years = (last_date - first_date).total_seconds() / (365.25 * 86400)
            if np.isfinite(years) and years > 0:
                annualized_return = float((1 + tr) ** (1 / years) - 1)
        except (TypeError, ValueError):
            pass

    if len(rets) < 2:
        sr = None
        volatility = None
    else:
        daily_std = rets.std(ddof=1)
        volatility = float(daily_std * np.sqrt(252)) if np.isfinite(daily_std) else None
        if not np.isfinite(daily_std) or daily_std == 0:
            sr = None
        else:
            excess = rets - risk_free_rate / 252
            sr = float(np.sqrt(252) * excess.mean() / daily_std)

    if "performance_index" in results:
        performance = pd.to_numeric(results["performance_index"], errors="coerce")
    else:
        # This fallback supports older result tables; simulations use performance_index.
        performance = pd.to_numeric(
            results.get("portfolio_value", pd.Series(dtype=float)), errors="coerce"
        )
    performance = performance[np.isfinite(performance) & (performance >= 0)]
    if not performance.empty:
        running_peak = performance.cummax().replace(0, np.nan)
        drawdown = performance.div(running_peak).sub(1)
        drawdown = drawdown[np.isfinite(drawdown)]
        max_drawdown = float(drawdown.min()) if not drawdown.empty else None
    else:
        max_drawdown = None

    return {
        "final_value": fv,
        "total_return": tr,
        "total_contributions": total_contributions,
        "annualized_return": annualized_return,
        "sharpe_ratio": sr,
        "max_drawdown": max_drawdown,
        "annualized_volatility": volatility,
    }
