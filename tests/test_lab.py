import numpy as np
import pandas as pd
import pytest

from analysis.lab import (
    STRATEGY_MA, STRATEGY_ML, LabError, explain_results, run_lab_experiment, score_prediction,
)
from backtest.engine import calculate_stats, run_simulation
from strategies.benchmark import buy_hold_strategy


def prices(closes, start="2021-01-04"):
    idx = pd.bdate_range(start, periods=len(closes))
    return pd.DataFrame({"close": closes}, index=idx, dtype=float)


@pytest.fixture
def long_prices():
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2018-01-01", "2022-12-30")
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, len(idx))))
    return pd.DataFrame({"open": close, "high": close * 1.01, "low": close * 0.99, "close": close,
                         "volume": 1000.0}, index=idx)


# ---------- trading costs in the engine ----------

def test_zero_cost_matches_original_behavior():
    data = prices([100, 110, 121])
    res = run_simulation(data, buy_hold_strategy(data), starting_money=1000)
    assert res["portfolio_value"].iloc[-1] == pytest.approx(1210)


def test_costs_charged_on_every_position_change():
    data = prices([100.0] * 5)
    sig = pd.DataFrame({"signal": [1, 1, 0, 1, 1]}, index=data.index)
    res = run_simulation(data, sig, starting_money=1000, cost_per_trade=0.01)
    assert res["trade"].sum() == 3  # buy, sell, buy
    assert res["portfolio_value"].iloc[-1] == pytest.approx(1000 * 0.99 ** 3)


def test_buy_hold_pays_one_entry_cost_even_with_start_date():
    data = prices([100, 100, 110, 121])
    res = run_simulation(data, buy_hold_strategy(data), starting_money=1000, cost_per_trade=0.01,
                         start_date=data.index[2])
    assert res["trade"].sum() == 1
    assert res["strategy_return"].iloc[0] == pytest.approx(0.10 - 0.01)


def test_invalid_cost_rejected():
    data = prices([1.0, 2.0])
    with pytest.raises(ValueError):
        run_simulation(data, buy_hold_strategy(data), cost_per_trade=1.5)


# ---------- lab experiments ----------

def test_ma_experiment_runs_and_compounds(long_prices):
    r = run_lab_experiment(long_prices, STRATEGY_MA, 20, 50, cost_per_trade=0.001)
    assert r["s"]["num_trades"] > 0
    assert 0 < r["s"]["time_in_market"] < 1
    assert r["b"]["num_trades"] == 1
    assert r["b"]["time_in_market"] == pytest.approx(1, abs=0.01)
    yearly = r["yearly"]
    assert (1 + yearly["strategy"]).prod() - 1 == pytest.approx(r["s"]["total_return"])
    assert list(yearly.index) == [2018, 2019, 2020, 2021, 2022]


def test_ml_experiment_scores_both_on_unseen_window_only(long_prices):
    r = run_lab_experiment(long_prices, STRATEGY_ML)
    start = r["evaluation_start"]
    assert start is not None
    assert r["strat_res"].index[0] == start == r["bench_res"].index[0]
    # The holdout is roughly the last 20% of the period.
    assert len(r["strat_res"]) < 0.25 * len(long_prices)


def test_too_little_data_gives_friendly_error():
    with pytest.raises(LabError):
        run_lab_experiment(prices(list(range(1, 40))), STRATEGY_MA, 20, 50)


# ---------- scoring & explanations ----------

def stats(final, ret, dd, sharpe=0.5, trades=10, tim=0.6):
    return {"final_value": final, "total_return": ret, "max_drawdown": dd, "sharpe_ratio": sharpe,
            "num_trades": trades, "time_in_market": tim}


def test_score_prediction():
    s, b = stats(12000, 0.20, -0.15), stats(13000, 0.30, -0.25)
    rows = score_prediction({"winner": "strategy", "bench_return": 0.35, "bench_drawdown": 0.50}, s, b)
    assert [r["correct"] for r in rows] == [False, True, False]
    assert rows[0]["actual"] == "benchmark"
    assert rows[2]["actual"] == pytest.approx(0.25)


def test_explanations_mention_costs_drawdown_and_ai_holdout():
    notes = " ".join(explain_results(STRATEGY_ML, stats(12000, 0.2, -0.10), stats(13000, 0.3, -0.30), 0.001))
    assert "Buy-and-hold came out ahead" in notes
    assert "10 trades" in notes
    assert "smaller than buy-and-hold" in notes
    assert "never seen" in notes
