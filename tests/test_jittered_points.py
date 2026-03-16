"""Tests for jittered points in ridgeline plots."""

import numpy as np
import pandas as pd
import pytest
from plotnine import aes, ggplot

from ridgenine import geom_density_ridges
from ridgenine.stat_density_ridges import stat_density_ridges


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
    result = s.compute_panel(df, scales)
    return result, s


@pytest.fixture
def simple_df():
    rng = np.random.default_rng(42)
    return pd.concat(
        [
            pd.DataFrame({"x": rng.normal(i, 1, 50), "y": cat})
            for i, cat in enumerate(["A", "B", "C"])
        ],
        ignore_index=True,
    )


class TestStatOutput:
    def test_jittered_points_stashes_data(self, simple_df):
        _, s = _compute(simple_df, jittered_points=True)
        jitter_data = s.params.get("_jitter_data")
        assert jitter_data is not None
        assert len(jitter_data) == 3  # 3 groups

    def test_point_data_has_jitter(self, simple_df):
        _, s = _compute(simple_df, jittered_points=True)
        combined = pd.concat(s.params["_jitter_data"], ignore_index=True)
        assert "point_jitter" in combined.columns
        assert (combined["point_jitter"] >= 0).all()
        assert (combined["point_jitter"] <= 1).all()

    def test_no_points_by_default(self, simple_df):
        _, s = _compute(simple_df)
        assert s.params.get("_jitter_data") is None

    def test_point_seed_reproducible(self, simple_df):
        _, s1 = _compute(simple_df, jittered_points=True, point_seed=42)
        _, s2 = _compute(simple_df, jittered_points=True, point_seed=42)
        p1 = pd.concat(s1.params["_jitter_data"])["point_jitter"].values
        p2 = pd.concat(s2.params["_jitter_data"])["point_jitter"].values
        np.testing.assert_array_equal(p1, p2)

    def test_different_seeds_differ(self, simple_df):
        _, s1 = _compute(simple_df, jittered_points=True, point_seed=1)
        _, s2 = _compute(simple_df, jittered_points=True, point_seed=2)
        p1 = pd.concat(s1.params["_jitter_data"])["point_jitter"].values
        p2 = pd.concat(s2.params["_jitter_data"])["point_jitter"].values
        assert not np.allclose(p1, p2)

    def test_point_count_matches_input(self, simple_df):
        _, s = _compute(simple_df, jittered_points=True)
        total = sum(len(d) for d in s.params["_jitter_data"])
        assert total == len(simple_df)


class TestRendering:
    def test_jittered_points_render(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(jittered_points=True)
        p.save(tmp_path / "jittered.png", verbose=False)

    def test_jittered_points_with_fill(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y", fill="y")) + geom_density_ridges(
            jittered_points=True, alpha=0.7
        )
        p.save(tmp_path / "jittered_fill.png", verbose=False)

    def test_jittered_points_custom_appearance(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(
            jittered_points=True,
            point_size=1.0,
            point_alpha=0.5,
            point_color="red",
            point_shape="D",
        )
        p.save(tmp_path / "jittered_custom.png", verbose=False)

    def test_jittered_points_with_quantile_lines(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(
            jittered_points=True, quantile_lines=True
        )
        p.save(tmp_path / "jittered_quantile.png", verbose=False)
