import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def simple_df():
    """Three string categories, 50 observations each."""
    rng = np.random.default_rng(42)
    cats = ["A", "B", "C"]
    return pd.concat(
        [pd.DataFrame({"x": rng.normal(i, 1, 50), "y": cat}) for i, cat in enumerate(cats)],
        ignore_index=True,
    )


@pytest.fixture
def numeric_y_df():
    """Three numeric y values, 30 observations each."""
    rng = np.random.default_rng(0)
    return pd.concat(
        [pd.DataFrame({"x": rng.normal(y * 2, 1, 30), "y": float(y)}) for y in [1, 2, 3]],
        ignore_index=True,
    )
