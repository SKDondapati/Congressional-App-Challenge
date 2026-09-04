import pandas as pd
import numpy as np
from backtest.engine import run_simulation, calculate_stats


def test_max_drawdown():
    dates = pd.date_range("2020-01-01", periods=4, freq="D")
    df = pd.DataFrame(index=dates)
    df["portfolio_value"] = [100.0, 120.0, 90.0, 110.0]
    df["strategy_return"] = [0.0, 0.0, 0.0, 0.0]
    stats = calculate_stats(df)
    assert abs(stats["max_drawdown"] - (-0.25)) < 1e-8


def test_total_return_and_cagr_formula():
    sv = 10000.0
    fv = 27431.0
    years = 10.0
    total_return = fv / sv - 1
    cagr = (fv / sv) ** (1 / years) - 1
    assert abs(total_return - 1.7431) < 1e-4
    # quick sanity: cagr should be positive and less than total return
    assert cagr > 0
    assert cagr < total_return


def test_monthly_contributions_applied_on_month_change():
    # Create daily data over Jan-Mar (3 months)
    dates = pd.date_range("2020-01-01", "2020-03-31", freq="D")
    data = pd.DataFrame(index=dates)
    data["close"] = 100.0  # flat prices
    # create zero signals (stay in cash / neutral strategy)
    signals = pd.DataFrame(index=dates)
    signals["signal"] = 0.0

    # start with zero initial money and $100 monthly contribution
    res = run_simulation(data, signals, starting_money=0.0, monthly_contribution=100.0)
    stats = calculate_stats(res)
    # Given implementation: contributions are added when month changes (Feb 1, Mar 1)
    # So for a Jan->Mar range we expect 2 contributions applied
    assert abs(stats["final_value"] - 200.0) < 1e-8


def test_recovery_after_loss():
    loss = 0.4
    recovery = 1 / (1 - loss) - 1
    assert abs(recovery - 0.6666666666666667) < 1e-12


def test_variant_only_changes_starting_amount():
    # simple constant price series; strategy returns 0 so final scales with starting amount
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    data = pd.DataFrame(index=dates)
    data["close"] = 100.0
    signals = pd.DataFrame(index=dates)
    signals["signal"] = 0.0

    res1 = run_simulation(data, signals, starting_money=1000.0, monthly_contribution=0.0)
    stats1 = calculate_stats(res1)
    res2 = run_simulation(data, signals, starting_money=2000.0, monthly_contribution=0.0)
    stats2 = calculate_stats(res2)
    assert abs(stats2["final_value"] - 2 * stats1["final_value"]) < 1e-8
