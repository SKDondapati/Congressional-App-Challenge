from data.data_manager import download_market_data, clean_price_data
from backtest.engine import run_simulation, calculate_stats

def dummy_strategy(data):
    signals = data.copy()
    signals['signal'] = 1
    signals['position'] = 0
    signals.loc[signals.index[0], 'position'] = 1
    return signals

if __name__ == "__main__":
    ticker = input("Enter ticker (e.g., AAPL): ") or "AAPL"
    start = input("Enter start date (YYYY-MM-DD): ") or "2020-01-01"
    end = input("Enter end date (YYYY-MM-DD): ") or "2023-12-31"
    
    print(f"\nLoading {ticker} data from {start} to {end}...")
    raw = download_market_data(ticker, start, end)
    
    if raw is None or raw.empty:
        print("Could not load data. Exiting.")
        exit()
    
    data = clean_price_data(raw)
    print(f"Loaded {len(data)} days of data.")
    
    print("Running dummy backtest (all buy, no sell)...")
    signals = dummy_strategy(data)
    results = run_simulation(data, signals)
    stats = calculate_stats(results)
    
    print("\n--- RESULTS ---")
    print(f"Final portfolio value: ${stats['final_value']:.2f}")
    print(f"Total return: {stats['total_return']:.2%}")
    print(f"Sharpe ratio: {stats['sharpe_ratio']:.2f}")
    print(f"Max drawdown: {stats['max_drawdown']:.2%}")
