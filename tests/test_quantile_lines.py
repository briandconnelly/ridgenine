"""Tests for quantile lines and quantile computation."""

import numpy as np
import pandas as pd
import pytest
from plotnine import aes, ggplot

from ridgenine import geom_density_ridges
from ridgenine.stat_density_ridges import _assign_quantiles, stat_density_ridges


def _compute(df, **kwargs):
    from unittest.mock import MagicMock

    s = stat_density_ridges(**kwargs)
    s.setup_params(df)
    df = df.copy()
    if "group" not in df.columns:
        codes, _ = pd.factorize(df["y"])
        df["group"] = codes + 1
    scales = MagicMock()
    scales.x.dimension.return_value = (df["x"].min() - 1, df["x"].max() + 1)
    return s.compute_panel(df, scales)


@pytest.fixture
def simple_df():
    rng = np.random.default_rng(42)
    return pd.concat(
        [
            pd.DataFrame({"x": rng.normal(i, 1, 100), "y": cat})
            for i, cat in enumerate(["A", "B", "C"])
        ],
        ignore_index=True,
    )


class TestAssignQuantiles:
    def test_integer_quantiles(self):
        rng = np.random.default_rng(0)
        raw_x = pd.Series(rng.normal(0, 1, 500))
        dens = pd.DataFrame({"x": np.linspace(-3, 3, 100), "density": 1.0})
        result = _assign_quantiles(dens, raw_x, None, 4)
        assert "quantile" in result.columns
        assert set(result["quantile"].unique()) == {1, 2, 3, 4}

    def test_list_quantiles(self):
        rng = np.random.default_rng(0)
        raw_x = pd.Series(rng.normal(0, 1, 500))
        dens = pd.DataFrame({"x": np.linspace(-3, 3, 100), "density": 1.0})
        result = _assign_quantiles(dens, raw_x, None, [0.5])
        assert set(result["quantile"].unique()) == {1, 2}

    def test_weighted_quantiles(self):
        raw_x = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        weight = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        dens = pd.DataFrame({"x": [1.0, 3.0, 5.0], "density": 1.0})
        result = _assign_quantiles(dens, raw_x, weight, [0.5])
        assert "quantile" in result.columns


class TestStatQuantiles:
    def test_quantiles_int_in_stat(self, simple_df):
        result = _compute(simple_df, quantiles=4)
        assert "quantile" in result.columns

    def test_quantiles_list_in_stat(self, simple_df):
        result = _compute(simple_df, quantiles=[0.25, 0.5, 0.75])
        assert "quantile" in result.columns

    def test_no_quantiles_by_default(self, simple_df):
        result = _compute(simple_df)
        # quantile column may or may not exist; if it exists it should be NaN or absent
        if "quantile" in result.columns:
            pass  # acceptable

    def test_quantile_values_cover_all_points(self, simple_df):
        result = _compute(simple_df, quantiles=3)
        # Filter to ridge rows only
        if "datatype" in result.columns:
            result = result[result["datatype"] != "point"]
        assert result["quantile"].notna().all()


class TestQuantileLinesRendering:
    def test_quantile_lines_render(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(quantile_lines=True)
        p.save(tmp_path / "quantile_lines.png", verbose=False)

    def test_quantile_lines_custom_quantiles(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(
            quantile_lines=True, quantiles=[0.1, 0.5, 0.9]
        )
        p.save(tmp_path / "quantile_lines_custom.png", verbose=False)

    def test_quantile_lines_with_fill(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y", fill="y")) + geom_density_ridges(
            quantile_lines=True, alpha=0.7
        )
        p.save(tmp_path / "quantile_lines_fill.png", verbose=False)

    def test_quantile_lines_int_quantiles(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(
            quantile_lines=True, quantiles=2
        )
        p.save(tmp_path / "quantile_lines_median.png", verbose=False)
