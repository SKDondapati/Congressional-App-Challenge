from data.data_manager import download_market_data, clean_price_data
from backtest.engine import run_simulation, calculate_stats
from strategies.moving_average import moving_average_strategy
from strategies.benchmark import buy_hold_strategy

def run_strategy_test(ticker, start_date, end_date, strategy_name, strategy_func, **kwargs):
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
    ticker = input("Enter ticker (e.g., AAPL): ") or "AAPL"
    start = input("Enter start date (YYYY-MM-DD): ") or "2020-01-01"
    end = input("Enter end date (YYYY-MM-DD): ") or "2023-12-31"
    
    print("\n" + "="*50)
    print("QUANTLIT - STRATEGY COMPARISON")
    print("="*50)
    
    ma_stats = run_strategy_test(
        ticker, start, end, 
        "Moving Average (20/50)", 
        moving_average_strategy,
        short_window=20, long_window=50
    )
    
    bh_stats = run_strategy_test(
        ticker, start, end, 
        "Buy & Hold", 
        buy_hold_strategy
    )
    
    if ma_stats and bh_stats:
        print("\n" + "="*50)
        print("COMPARISON")
        print("="*50)
        print(f"Moving Average return: {ma_stats['total_return']:.2%}")
        print(f"Buy & Hold return:     {bh_stats['total_return']:.2%}")
        
        if ma_stats['total_return'] > bh_stats['total_return']:
            print("\nMoving Average outperformed Buy & Hold")
        else:
            print("\nBuy & Hold outperformed Moving Average")