"""Tests for stat_binline."""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from plotnine import aes, ggplot

from ridgenine import geom_ridgeline
from ridgenine.stat_binline import stat_binline


def _compute(df, **kwargs):
    s = stat_binline(**kwargs)
    df = df.copy()
    if "group" not in df.columns:
        codes, _ = pd.factorize(df["y"])
        df["group"] = codes + 1
    scales = MagicMock()
    scales.x.dimension.return_value = (df["x"].min() - 0.5, df["x"].max() + 0.5)
    return s.compute_group(df[df["group"] == 1].reset_index(drop=True), scales)


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


class TestOutputColumns:
    def test_has_expected_columns(self, simple_df):
        result = _compute(simple_df)
        for col in ("x", "y", "density", "ndensity", "count", "ncount"):
            assert col in result.columns, f"missing column: {col}"

    def test_ndensity_range(self, simple_df):
        result = _compute(simple_df)
        assert result["ndensity"].between(0, 1).all()

    def test_ndensity_max_is_one(self, simple_df):
        result = _compute(simple_df)
        assert pytest.approx(result["ndensity"].max()) == 1.0

    def test_ncount_max_is_one(self, simple_df):
        result = _compute(simple_df)
        assert pytest.approx(result["ncount"].max()) == 1.0

    def test_y_preserved(self, simple_df):
        result = _compute(simple_df)
        assert (result["y"] == "A").all()


class TestBinParams:
    def test_custom_bins(self, simple_df):
        result = _compute(simple_df, bins=10)
        # Step function: 2 points per bin + 2 pad = ~22
        assert len(result) > 0

    def test_binwidth(self, simple_df):
        result = _compute(simple_df, binwidth=0.5)
        assert len(result) > 0

    def test_breaks(self, simple_df):
        result = _compute(simple_df, breaks=[-3, -1, 0, 1, 3])
        assert len(result) > 0

    def test_boundary(self, simple_df):
        result = _compute(simple_df, binwidth=1.0, boundary=0.0)
        assert len(result) > 0

    def test_center(self, simple_df):
        result = _compute(simple_df, binwidth=1.0, center=0.5)
        assert len(result) > 0

    def test_no_pad(self, simple_df):
        r_pad = _compute(simple_df, bins=10, pad=True)
        r_nopad = _compute(simple_df, bins=10, pad=False)
        assert len(r_nopad) < len(r_pad)


class TestIntegration:
    def test_renders_with_geom_ridgeline(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_ridgeline(stat="binline")
        p.save(tmp_path / "binline.png", verbose=False)

    def test_renders_with_bins_param(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_ridgeline(stat="binline", bins=15)
        p.save(tmp_path / "binline_bins.png", verbose=False)

    def test_renders_with_fill(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y", fill="y")) + geom_ridgeline(
            stat="binline", alpha=0.7
        )
        p.save(tmp_path / "binline_fill.png", verbose=False)
