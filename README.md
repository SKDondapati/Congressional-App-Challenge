# Congressional-App-Challenge

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

## Notes

- `data/data_manager.py` depends on `yfinance` to download market data.
- `backtest/engine.py` depends on `pandas` and `numpy`.
- On macOS, use `python3` if `python` is not available.
