import pandas as pd
import pytest

from backtest.engine import calculate_stats, run_simulation
from analysis.comparison import compare_results
from strategies.benchmark import buy_hold_strategy
from strategies.ml_predictor import ml_predictor_strategy
from strategies.moving_average import moving_average_strategy


def test_strategy_signals_and_stats_are_compatible():
    df = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            "high": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            "low": [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
            "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
        },
        index=pd.date_range("2020-01-01", periods=10, freq="D"),
    )

    ma_signals = moving_average_strategy(df, short_window=2, long_window=3)
    bh_signals = buy_hold_strategy(df)
    ml_signals = ml_predictor_strategy(df)

    assert "signal" in ma_signals.columns
    assert "signal" in bh_signals.columns
    assert "signal" in ml_signals.columns

    ma_results = run_simulation(df, ma_signals)
    bh_results = run_simulation(df, bh_signals)
    ml_results = run_simulation(df, ml_signals)

    ma_stats = calculate_stats(ma_results)
    bh_stats = calculate_stats(bh_results)
    ml_stats = calculate_stats(ml_results)

    assert set(ma_stats).issuperset(
        {"final_value", "total_return", "sharpe_ratio", "max_drawdown"}
    )
    assert set(bh_stats).issuperset(
        {"final_value", "total_return", "sharpe_ratio", "max_drawdown"}
    )
    assert set(ml_stats).issuperset(
        {"final_value", "total_return", "sharpe_ratio", "max_drawdown"}
    )


def test_strategies_use_valid_signals_and_ma_waits_for_history(sample_prices):
    moving = moving_average_strategy(sample_prices, short_window=5, long_window=20)
    benchmark = buy_hold_strategy(sample_prices)
    ml = ml_predictor_strategy(sample_prices)

    for signals in (moving, benchmark, ml):
        assert signals.index.equals(sample_prices.index)
        assert signals["signal"].isin([0, 1]).all()
    assert moving["signal"].iloc[:19].eq(0).all()


def test_moving_average_flat_falling_and_crossover_prices():
    examples = [
        ([5, 5, 5, 5, 5], 0),
        ([5, 4, 3, 2, 1], 0),
        ([3, 2, 1, 2, 4, 6], 1),
    ]
    for prices, last_signal in examples:
        data = pd.DataFrame({"close": prices})
        signals = moving_average_strategy(data, short_window=2, long_window=3)
        assert signals["signal"].iloc[:2].eq(0).all()
        assert signals["signal"].iloc[-1] == last_signal


def test_ml_and_benchmark_share_the_out_of_sample_dates(sample_prices):
    ml_signals = ml_predictor_strategy(sample_prices)
    prediction_dates = ml_signals.index[ml_signals["evaluation_prediction"]]
    assert len(prediction_dates) > 0
    assert ml_signals.loc[: prediction_dates[0], "signal"].iloc[:-1].eq(0).all()

    evaluation_start = sample_prices.index[
        sample_prices.index.get_loc(prediction_dates[0]) + 1
    ]
    ml_results = run_simulation(
        sample_prices, ml_signals, starting_money=1000, start_date=evaluation_start
    )
    benchmark_results = run_simulation(
        sample_prices,
        buy_hold_strategy(sample_prices),
        starting_money=1000,
        start_date=evaluation_start,
    )
    assert ml_results.index.equals(benchmark_results.index)
    assert ml_results.index[0] == evaluation_start

    comparison = compare_results(
        {"ML Predictor": ml_results, "Buy & Hold": benchmark_results}
    )
    assert comparison["strategy"].tolist() == ["ML Predictor", "Buy & Hold"]
    assert "annualized_volatility" in comparison.columns


def test_strategy_parameters_are_valid():
    with pytest.raises(ValueError):
        moving_average_strategy(pd.DataFrame({"close": [1, 2]}), 5, 5)
    with pytest.raises(ValueError):
        ml_predictor_strategy(pd.DataFrame({"close": [1, 2]}), test_size=1)
