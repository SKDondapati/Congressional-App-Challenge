import subprocess
import sys

from backtest.engine import calculate_stats, run_simulation
from data.data_manager import clean_price_data, download_market_data
from strategies.benchmark import buy_hold_strategy
from strategies.ml_predictor import ml_predictor_strategy
from strategies.moving_average import moving_average_strategy


def run_strategy_test(
    ticker, start_date, end_date, strategy_name, strategy_func, **kwargs
):
    print(f"\n--- Testing {strategy_name} on {ticker} ---")

    raw = download_market_data(ticker, start_date, end_date)
    if raw is None or raw.empty:
        print("Could not load data.")
        return None

    data = clean_price_data(raw)
    print(f"Loaded {len(data)} days of data.")

    signals = strategy_func(data, **kwargs) if kwargs else strategy_func(data)
    results = run_simulation(data, signals)
    stats = calculate_stats(results)

    print(f"Final value: ${stats['final_value']:.2f}")
    print(f"Total return: {stats['total_return']:.2%}")
    print(f"Sharpe ratio: {stats['sharpe_ratio']:.2f}")
    print(f"Max drawdown: {stats['max_drawdown']:.2%}")

    return stats


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--streamlit":
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "ui/app_interface.py"],
            check=False,
        )
        raise SystemExit

    ticker = input("Enter ticker (e.g., AAPL): ") or "AAPL"
    start = input("Enter start date (YYYY-MM-DD): ") or "2020-01-01"
    end = input("Enter end date (YYYY-MM-DD): ") or "2023-12-31"

    print("\n" + "=" * 50)
    print("QUANTLIT - STRATEGY COMPARISON (MA vs ML vs Buy & Hold)")
    print("=" * 50)

    ma_stats = run_strategy_test(
        ticker,
        start,
        end,
        "Moving Average (20/50)",
        moving_average_strategy,
        short_window=20,
        long_window=50,
    )

    ml_stats = run_strategy_test(
        ticker,
        start,
        end,
        "ML Predictor (Random Forest)",
        ml_predictor_strategy,
        lookback=5,
        test_size=0.2,
    )

    bh_stats = run_strategy_test(ticker, start, end, "Buy & Hold", buy_hold_strategy)

    if ma_stats and ml_stats and bh_stats:
        print("\n" + "=" * 50)
        print("FINAL COMPARISON")
        print("=" * 50)
        print(f"Moving Average return:  {ma_stats['total_return']:.2%}")
        print(f"ML Predictor return:    {ml_stats['total_return']:.2%}")
        print(f"Buy & Hold return:      {bh_stats['total_return']:.2%}")

        best = max(
            [
                (ma_stats["total_return"], "Moving Average"),
                (ml_stats["total_return"], "ML Predictor"),
                (bh_stats["total_return"], "Buy & Hold"),
            ],
            key=lambda x: x[0],
        )
        print(f"\n🏆 Winner: {best[1]} with {best[0]:.2%} return")
