# Congressional-App-Challenge

This project is a simple quantitative finance prototype that compares a moving-average strategy against a buy-and-hold strategy using historical stock data.

## Installation

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

When prompted, enter a ticker symbol (for example `AAPL`) and a date range in `YYYY-MM-DD` format.

## How the project works

The app follows this flow:

1. It downloads market data.
2. It cleans and prepares the price data.
3. It creates trading signals with a strategy.
4. It simulates portfolio performance.
5. It prints performance statistics for comparison.

## File-by-file explanation

### main.py

```python
from data.data_manager import download_market_data, clean_price_data
```
Imports the functions that download and prepare stock market data.

```python
from backtest.engine import run_simulation, calculate_stats
```
Imports the simulation and performance-statistics functions.

```python
from strategies.moving_average import moving_average_strategy
```
Imports the moving-average trading strategy.

```python
from strategies.benchmark import buy_hold_strategy
```
Imports the benchmark strategy that buys and holds the asset.

```python
def run_strategy_test(ticker, start_date, end_date, strategy_name, strategy_func, **kwargs):
```
Defines a reusable function to test any strategy on a chosen ticker and date range.

```python
print(f"\n--- Testing {strategy_name} on {ticker} ---")
```
Prints a heading to the console so the user can see which strategy is being tested.

```python
raw = download_market_data(ticker, start_date, end_date)
```
Downloads the raw stock data from the internet.

```python
if raw is None or raw.empty:
```
Checks whether the download succeeded and whether the data contains any rows.

```python
print("Could not load data.")
return None
```
Stops the function gracefully if no usable data was found.

```python
data = clean_price_data(raw)
```
Cleans the raw data into a simpler format with the columns needed for analysis.

```python
print(f"Loaded {len(data)} days of data.")
```
Shows how many rows of price history were loaded.

```python
signals = strategy_func(data, **kwargs) if kwargs else strategy_func(data)
```
Runs the selected strategy to produce buy/sell signals based on the cleaned data.

```python
results = run_simulation(data, signals)
```
Runs the backtest using the price data and the generated signals.

```python
stats = calculate_stats(results)
```
Calculates portfolio performance results like final value and return.

```python
print(f"Final value: ${stats['final_value']:.2f}")
```
Prints the final portfolio value in dollars.

```python
print(f"Total return: {stats['total_return']:.2%}")
```
Prints the total return as a percentage.

```python
print(f"Sharpe ratio: {stats['sharpe_ratio']:.2f}")
```
Prints the Sharpe ratio, which measures risk-adjusted return.

```python
print(f"Max drawdown: {stats['max_drawdown']:.2%}")
```
Prints the largest portfolio decline from a previous peak.

```python
return stats
```
Returns the statistics so the caller can use them later.

```python
if __name__ == "__main__":
```
Ensures the code only runs when this file is executed directly, not when imported elsewhere.

```python
ticker = input("Enter ticker (e.g., AAPL): ") or "AAPL"
```
Asks the user for a stock ticker and uses `AAPL` as the default if nothing is entered.

```python
start = input("Enter start date (YYYY-MM-DD): ") or "2020-01-01"
```
Asks for the start date and defaults to January 1, 2020.

```python
end = input("Enter end date (YYYY-MM-DD): ") or "2023-12-31"
```
Asks for the end date and defaults to December 31, 2023.

```python
ma_stats = run_strategy_test(...)
```
Runs the moving-average strategy test.

```python
bh_stats = run_strategy_test(...)
```
Runs the buy-and-hold benchmark test.

```python
if ma_stats and bh_stats:
```
Checks that both tests completed successfully before comparing them.

```python
print(f"Moving Average return: {ma_stats['total_return']:.2%}")
```
Prints the moving-average strategy return for comparison.

```python
print(f"Buy & Hold return:     {bh_stats['total_return']:.2%}")
```
Prints the buy-and-hold return for comparison.

```python
if ma_stats['total_return'] > bh_stats['total_return']:
```
Compares which strategy performed better over the selected time period.

### data/data_manager.py

```python
import yfinance as yf
```
Imports the `yfinance` package used to retrieve stock market data.

```python
def download_market_data(ticker, start_date, end_date):
```
Defines a function to download historical data for a ticker over a date range.

```python
try:
```
Starts a block that safely handles possible download errors.

```python
df = yf.download(ticker, start=start_date, end=end_date)
```
Downloads historical market data from Yahoo Finance.

```python
if df.empty:
```
Checks whether the downloaded data is empty.

```python
print("No data found for that ticker.")
```
Prints a user-friendly message if the ticker has no data.

```python
return df
```
Returns the downloaded dataframe.

```python
except:
```
Catches any unexpected error during the download.

```python
print("Something went wrong downloading data.")
```
Prints an error message if the request fails.

```python
return None
```
Returns `None` so the calling code can handle the failure.

```python
def clean_price_data(raw_df):
```
Defines a function that prepares the downloaded data for strategy analysis.

```python
if raw_df is None or raw_df.empty:
```
Checks whether the input is missing or empty.

```python
return raw_df
```
Returns the input unchanged if there is no usable data.

```python
df = raw_df.copy()
```
Creates a copy so the original data is not modified.

```python
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
```
Keeps only the columns needed for analysis.

```python
df.columns = ['open', 'high', 'low', 'close', 'volume']
```
Renames the columns to lowercase for consistent access.

```python
df = df.dropna()
```
Removes rows with missing values so the backtest is cleaner.

```python
return df
```
Returns the cleaned dataframe.

### backtest/engine.py

```python
import pandas as pd
```
Imports pandas for working with tabular data.

```python
import numpy as np
```
Imports numpy for numerical calculations.

```python
def run_simulation(data, signals, starting_money=10000):
```
Defines the backtesting function that simulates portfolio growth.

```python
df = signals.copy()
```
Copies the signal dataframe so the original is not changed.

```python
df['daily_return'] = data['close'].pct_change().fillna(0)
```
Calculates each day’s percentage price change.

```python
df['strategy_return'] = df['signal'].shift(1).fillna(0) * df['daily_return']
```
Applies the previous day’s signal to today’s return to simulate trading.

```python
df['portfolio_value'] = (1 + df['strategy_return']).cumprod() * starting_money
```
Tracks the portfolio value over time using compounded returns.

```python
df['buy_hold_value'] = (1 + df['daily_return']).cumprod() * starting_money
```
Tracks a buy-and-hold benchmark value for comparison.

```python
return df
```
Returns the simulation results.

```python
def calculate_stats(results, risk_free_rate=0.0):
```
Defines a function to compute key performance statistics from the simulation output.

```python
if results is None or results.empty:
```
Checks whether the simulation results are valid.

```python
return {
```
Returns a default set of stats if there is no data.

```python
final_value = results['portfolio_value'].iloc[-1]
```
Gets the portfolio value from the last row of the simulation.

```python
start_value = results['portfolio_value'].iloc[0]
```
Gets the starting portfolio value.

```python
total_return = final_value / start_value - 1 if start_value != 0 else 0.0
```
Calculates the total portfolio return over the testing period.

```python
returns = results['strategy_return'].fillna(0)
```
Creates a series of strategy returns with missing values filled with zero.

```python
if len(returns) < 2 or returns.std(ddof=1) == 0:
```
Avoids computing a Sharpe ratio when there is not enough data or no variation.

```python
sharpe_ratio = 0.0
```
Sets the Sharpe ratio to zero in that edge case.

```python
excess_returns = returns - risk_free_rate / 252
```
Adjusts returns by the assumed risk-free rate.

```python
sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std(ddof=1)
```
Calculates the annualized Sharpe ratio.

```python
cum_max = results['portfolio_value'].cummax()
```
Computes the running maximum portfolio value.

```python
drawdown = (results['portfolio_value'] - cum_max) / cum_max
```
Measures how far portfolio value is below its previous peak.

```python
max_drawdown = drawdown.min() if not drawdown.empty else 0.0
```
Finds the worst drawdown in the backtest.

```python
return {
```
Returns a dictionary of summary statistics.

### strategies/moving_average.py

```python
import pandas as pd
```
Imports pandas to work with the price data as a dataframe.

```python
def moving_average_strategy(data, short_window=20, long_window=50):
```
Defines the moving-average trading strategy.

```python
signals = data.copy()
```
Copies the input data so the strategy does not mutate the original dataframe.

```python
signals['short_ma'] = signals['close'].rolling(window=short_window, min_periods=1).mean()
```
Calculates the short moving average over the selected window.

```python
signals['long_ma'] = signals['close'].rolling(window=long_window, min_periods=1).mean()
```
Calculates the long moving average.

```python
signals['signal'] = 0
```
Initializes the signal column with no position.

```python
signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
```
Creates a buy signal when the short moving average is above the long moving average.

```python
signals.loc[signals['short_ma'] <= signals['long_ma'], 'signal'] = 0
```
Creates a hold or no-position signal otherwise.

```python
signals['position'] = signals['signal'].diff()
```
Marks when the signal changes from one day to the next.

```python
return signals
```
Returns the dataframe containing the generated signals.

### strategies/benchmark.py

```python
def buy_hold_strategy(data):
```
Defines the benchmark strategy that always holds the asset.

```python
signals = data.copy()
```
Copies the input dataframe.

```python
signals['signal'] = 1
```
Sets the signal to buy at every row.

```python
signals['position'] = 0
```
Initializes the position tracking column.

```python
signals.loc[signals.index[0], 'position'] = 1
```
Marks the first row as the initial buy entry.

```python
return signals
```
Returns the benchmark signals.

## Notes

- `data/data_manager.py` depends on `yfinance` to download market data.
- `backtest/engine.py` depends on `pandas` and `numpy`.
- On macOS, use `python3` if `python` is not available.
