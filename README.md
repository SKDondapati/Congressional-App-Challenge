# QuantLit

QuantLit is a student-built investing simulator for people who are new to investing. It lets users explore how simple strategies behaved in historical market data, see the effect of contributions, and compare return with risk without using real money. It is designed to support learning; its impact has not been measured in a user study.

## What You Can Explore

- Compare buy-and-hold, moving-average, and Random Forest signals on historical prices.
- Change an initial balance, monthly deposits, strategy, and date range.
- Review ending balance, total contributions, time-weighted return, drawdown, volatility, and Sharpe ratio.
- Compare strategies on the same dates, including an out-of-sample ML period and a buy-and-hold baseline.
- Make a risk prediction before comparing strategies, then inspect a real historical decline in the selected data.
- Read beginner explanations or view the methodology and assumptions.

## Install

QuantLit is tested with Python 3.12. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For tests, install the development requirements instead:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Run

Start the web app with:

```bash
python -m streamlit run ui/app_interface.py
```

Streamlit prints a local URL, usually `http://localhost:8501`.

The optional command-line comparison is separate:

```bash
python main.py
```

## How Results Are Calculated

- A strategy signal from the previous trading day is applied to the next day's price return. Signals are not allowed to use that next day's closing price.
- The initial balance is present on the first selected date. Monthly deposits are added before returns on the first trading day of each later month in the selected range.
- Investment return compounds the strategy's daily returns, so deposits are not counted as investment gains. The app also reports the total initial balance and deposits.
- Drawdown is calculated from a performance index without cash deposits. The account-value chart still includes deposits.
- Sharpe and volatility use daily strategy returns and 252 trading days. Sharpe assumes a 0% annual risk-free rate unless a caller supplies another rate.
- The ML strategy trains chronologically on the earlier data and reports predictions only for its later holdout period. Its comparison uses the same dates as the buy-and-hold baseline.

## Strategy Notes

- **Buy & Hold** stays invested throughout the selected period.
- **Moving Average** is invested only when its short average is above its long average. It stays neutral until the full long window is available.
- **ML Predictor** is a small Random Forest experiment, not a forecast. It needs enough price history to train and tests on a later chronological holdout. Buy-and-hold is the simple baseline.

## Data and Limitations

Historical prices are downloaded from Yahoo Finance with `yfinance`; downloads need an internet connection and can fail or change. Individual-stock prices may not include dividends. Results are historical simulations, not predictions or investment advice. The simulator does not model fees, taxes, slippage, or trading constraints. The inflation chart uses an illustrative 2% assumption, not measured inflation for the selected dates. Cash-savings and real-estate comparisons are not implemented.

The Hindi and Spanish interface translations cover only some strings and have not been reviewed by fluent financial translators. They should not be treated as complete translations.

## Project Layout

- `data/`: download and clean price history.
- `strategies/`: buy-and-hold, moving-average, and ML signals.
- `backtest/`: portfolio simulation and performance statistics.
- `analysis/`: shared strategy comparison table.
- `ui/`: Streamlit app and explanations.
- `tests/`: offline tests using synthetic price data.

GitHub Actions runs the test suite on pushes and pull requests. Deployment and volunteer learning-impact testing still need to be completed before making claims about real-world educational outcomes.