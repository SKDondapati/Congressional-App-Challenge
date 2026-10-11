import os
import sys

import numpy as np
import pandas as pd
import pytest

# Ensure the project root is on sys.path so tests can import local packages
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def sample_prices():
    dates = pd.date_range("2020-01-01", periods=180, freq="B")
    close = 100 * np.cumprod(1 + 0.001 + 0.01 * np.sin(np.arange(len(dates)) / 5))
    return pd.DataFrame(
        {
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1000 + np.arange(len(dates)),
        },
        index=dates,
    )
