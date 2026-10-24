# QuantLit

QuantLit is a student-built financial-literacy lab for people who are new to investing. Students make a prediction, run strategies on historical market data, compare the calculated results, and consider what the experiment can and cannot show. It is designed to support learning; its impact has not been measured in a user study.

## What You Can Explore

- Compare buy-and-hold, moving-average, and Random Forest signals on historical prices.
- Change an initial balance, monthly deposits, strategy, and date range.
- Review ending balance, total contributions, time-weighted return, drawdown, volatility, and Sharpe ratio.
- Compare strategies on the same dates, including an out-of-sample ML period and a buy-and-hold baseline.
- **Prediction-versus-Reality Lab:** predict whether a moving-average rule or an AI predictor beats buy-and-hold (and guess the return and worst drop), lock it in, then see your score, the reasons behind the result, a year-by-year check, and the limits of the test.
- Add a trading cost per trade to see how fees affect strategies that trade often.
- Investigate an actual historical market decline and calculate how much a loss needs to recover.
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

After activating the virtual environment, start the web app with:

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
- Final account value includes deposits; investment gain/loss does not. Time-weighted investment return compounds daily strategy returns without treating deposits as gains.
- Annualized return is calculated from time-weighted return and elapsed calendar time, not from the ending account balance. It is undefined if the period is zero or the cumulative return is -100% or less.
- Drawdown is the largest decline from a previous high in the cumulative performance index, which excludes deposits. The account-value chart includes deposits.
- Annualized volatility and Sharpe use daily strategy returns and 252 trading days. Sharpe assumes a 0% annual risk-free rate. Sharpe is `N/A` with fewer than two valid observations or zero return variability.
- The ML model predicts the next day's direction from information available through the current close. Its chronological holdout signals are applied to the following day's return. Model comparisons use the same holdout dates as buy-and-hold; the model is an experiment, not a forecast.
- The selected end date is inclusive in the interface. The data request advances the provider's exclusive end boundary by one day.
- Multi-ticker portfolios are equal-weighted from daily returns on dates shared by all selected tickers. OHLC and volume are not invented when the source omits them.

## Educational Experiment Workflow

Open the **Prediction Lab** (the first page). Pick a stock, a period, and a strategy, then lock in a prediction: which approach ends with more money, buy-and-hold's total return, and its worst drop. QuantLit runs both approaches over the same dates and scores each guess. For the AI predictor, the model trains on the first 80% of the dates and both approaches are scored only on the final 20%, which the model never saw. **Practice data** (clearly labeled as simulated) keeps the Lab usable if Yahoo Finance is unavailable. Results describe history, not the future.

## Deploy

1. Push to GitHub (the `venv/` folder is ignored and should not be committed).
2. At https://share.streamlit.io, create an app from this repo with main file `ui/app_interface.py`.
3. Open the public link in a private window and on a phone to confirm it works.

## Architecture

- `data/` validates and cleans downloaded market prices and aligns multi-ticker price histories.
- `strategies/` creates buy-and-hold, moving-average, and chronological Random Forest signals.
- `backtest/` applies prior-day signals to next-day returns and tracks both account value and a deposit-free performance index.
- `analysis/` summarizes consistent strategy comparisons and identifies tied largest drawdowns.
- `ui/` provides the Streamlit experiment controls, charts, history, explanations, and learning resources.
- `tests/` uses synthetic data and mocked downloads for reproducible checks without relying on live prices.

## Strategy Notes

- **Buy & Hold** stays invested throughout the selected period.
- **Moving Average** is invested only when its short average is above its long average. It stays neutral until the full long window is available.
- **ML Predictor** is a small Random Forest experiment, not a forecast. It needs enough price history to train and tests on a later chronological holdout. Buy-and-hold is the simple baseline.

## Data and Limitations

Historical prices are downloaded from Yahoo Finance with `yfinance`; downloads need an internet connection and can fail or change. Individual-stock prices may not include dividends. Missing price dates are not fabricated. A multi-ticker portfolio uses dates shared by all tickers, which can shorten its usable history.

Results are historical simulations, not predictions or investment advice. The simulator currently models long-or-flat exposure and does not model transaction costs, fees, taxes, slippage, withdrawals, or trading constraints. It does not calculate money-weighted return. The inflation chart uses an illustrative 2% assumption, not measured inflation for the selected dates. Cash-savings and real-estate comparisons are not implemented.

The Hindi and Spanish interface translations cover only some strings and have not been reviewed by fluent financial translators. They should not be treated as complete translations.

## Project Layout

- `data/`: download and clean price history.
- `strategies/`: buy-and-hold, moving-average, and ML signals.
- `backtest/`: portfolio simulation and performance statistics.
- `analysis/`: shared strategy comparison table.
- `ui/`: Streamlit app and explanations.
- `tests/`: offline tests using synthetic price data.

GitHub Actions runs the test suite on pushes and pull requests. Deployment and volunteer learning-impact testing still need to be completed before making claims about real-world educational outcomes.

## Competition Demo Outline

1. Introduce the question: why can an investment with a positive return still have a difficult loss along the way?
2. In Beginner Mode, choose **Compare All** and state a drawdown hypothesis with a short reason.
3. Run one historical experiment and compare ending value, contributions, investment return, and drawdown.
4. Reveal which strategy had the largest drawdown, explain the result using the selected dates, then change one date or assumption and rerun.
5. Briefly explain that the backtest uses prior-day signals and that the Random Forest is evaluated on a later holdout period.
6. Close by noting that historical simulations are educational comparisons, not predictions or financial advice.