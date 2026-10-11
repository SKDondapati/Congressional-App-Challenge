from unittest.mock import patch

import pandas as pd
import pytest

from data.data_manager import (
    MarketDataError,
    clean_price_data,
    download_market_data,
    download_market_data_multi,
)


def test_clean_price_data_accepts_flat_and_multiindex_columns():
    dates = pd.date_range("2024-01-01", periods=2)
    flat = pd.DataFrame(
        {"Open": [10, 11], "High": [11, 12], "Low": [9, 10],
         "Close": [10, 11], "Volume": [100, 110]},
        index=dates,
    )
    multi = flat.copy()
    multi.columns = pd.MultiIndex.from_product([flat.columns, ["AAPL"]])

    assert clean_price_data(flat).columns.tolist() == [
        "open", "high", "low", "close", "volume"
    ]
    pd.testing.assert_frame_equal(clean_price_data(flat), clean_price_data(multi))


def test_clean_price_data_drops_duplicate_dates_and_invalid_closes():
    dates = pd.to_datetime(["2024-01-02", "2024-01-01", "2024-01-02"])
    prices = pd.DataFrame({"Close": [12, 10, 0]}, index=dates)

    cleaned = clean_price_data(prices)

    assert cleaned.index.is_monotonic_increasing
    assert cleaned.index.is_unique
    assert cleaned["close"].tolist() == [10]


def test_clean_price_data_requires_closing_prices():
    with pytest.raises(MarketDataError, match="closing prices"):
        clean_price_data(pd.DataFrame({"Open": [10]}))


def test_clean_price_data_drops_infinite_closes():
    cleaned = clean_price_data(pd.DataFrame({"Close": [10, float("inf")]}))

    assert cleaned["close"].tolist() == [10]


def test_download_market_data_reports_an_empty_response():
    with patch("data.data_manager.yf.download", return_value=pd.DataFrame()):
        with pytest.raises(MarketDataError, match="No market data was returned"):
            download_market_data("AAPL", "2024-01-01", "2024-02-01")


@pytest.mark.parametrize(
    "ticker,start,end",
    [("", "2024-01-01", "2024-02-01"), ("AAPL", "2024-02-01", "2024-01-01")],
)
def test_download_market_data_validates_request(ticker, start, end):
    with pytest.raises(MarketDataError):
        download_market_data(ticker, start, end)


def test_multi_ticker_download_uses_concat_and_unique_dates():
    dates = pd.date_range("2024-01-01", periods=3)
    first = pd.DataFrame({"Close": [100, 110, 110]}, index=dates)
    second = pd.DataFrame({"Close": [50, 50, 55]}, index=dates)

    with patch(
        "data.data_manager.download_market_data", side_effect=[first, second]
    ):
        result = download_market_data_multi("AAA,BBB", "2024-01-01", "2024-01-04")

    assert result.index.is_unique
    assert result["close"].tolist() == pytest.approx([75, 78.75, 82.6875])