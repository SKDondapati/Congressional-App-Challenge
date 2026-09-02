import pandas as pd

from strategies.moving_average import moving_average_strategy
from strategies.benchmark import buy_hold_strategy
from strategies.ml_predictor import ml_predictor_strategy
from backtest.engine import run_simulation, calculate_stats


def test_strategy_signals_and_stats_are_compatible():
    df = pd.DataFrame(
        {
            'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            'high': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
            'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
        },
        index=pd.date_range('2020-01-01', periods=10, freq='D'),
    )

    ma_signals = moving_average_strategy(df, short_window=2, long_window=3)
    bh_signals = buy_hold_strategy(df)
    ml_signals = ml_predictor_strategy(df)

    assert 'signal' in ma_signals.columns
    assert 'signal' in bh_signals.columns
    assert 'signal' in ml_signals.columns

    ma_results = run_simulation(df, ma_signals)
    bh_results = run_simulation(df, bh_signals)
    ml_results = run_simulation(df, ml_signals)

    ma_stats = calculate_stats(ma_results)
    bh_stats = calculate_stats(bh_results)
    ml_stats = calculate_stats(ml_results)

    assert set(ma_stats).issuberset({'final_value', 'total_return', 'sharpe_ratio', 'max_drawdown'})
    assert set(bh_stats).issuberset({'final_value', 'total_return', 'sharpe_ratio', 'max_drawdown'})
    assert set(ml_stats).issuberset({'final_value', 'total_return', 'sharpe_ratio', 'max_drawdown'})
