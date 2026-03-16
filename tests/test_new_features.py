"""Tests for rel_min_height, panel_scaling, and theme_ridges."""

import numpy as np
import pandas as pd
import pytest
from plotnine import aes, facet_wrap, ggplot
from plotnine.themes.theme import theme

from ridgenine import geom_density_ridges, geom_ridgeline, theme_ridges
from ridgenine.stat_density_ridges import stat_density_ridges

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def ridge_df():
    x = np.linspace(-3, 3, 40)
    frames = [
        pd.DataFrame({"x": x, "y": float(y), "height": np.exp(-0.5 * x**2)})
        for y in [1.0, 2.0, 3.0]
    ]
    return pd.concat(frames, ignore_index=True)


@pytest.fixture
def raw_df():
    rng = np.random.default_rng(42)
    return pd.concat(
        [
            pd.DataFrame({"x": rng.normal(i, 1, 50), "y": cat})
            for i, cat in enumerate(["A", "B", "C"])
        ],
        ignore_index=True,
    )


# ── rel_min_height ────────────────────────────────────────────────────────────


class TestRelMinHeight:
    def test_zero_has_no_effect(self, ridge_df):
        """Default rel_min_height=0 clips nothing."""
        g = geom_ridgeline(rel_min_height=0)
        result = g.setup_data(ridge_df.copy())
        assert (result["ymax"] >= result["ymin"]).all()

    def test_clips_tails(self, ridge_df):
        """rel_min_height=0.5 clips the gaussian tails below half-max."""
        g = geom_ridgeline(rel_min_height=0.5)
        result = g.setup_data(ridge_df.copy())
        # Heights below 50% of max (1.0) → ymax == ymin
        threshold = 0.5 * ridge_df["height"].max()
        below = result["height"] < threshold
        assert (result.loc[below, "ymax"] == result.loc[below, "ymin"]).all()
        # Heights above threshold should still be raised
        above = result["height"] >= threshold
        assert (result.loc[above, "ymax"] >= result.loc[above, "ymin"]).all()

    def test_full_clip(self, ridge_df):
        """rel_min_height=1.0 clips everything except the absolute peak."""
        g = geom_ridgeline(rel_min_height=1.0)
        result = g.setup_data(ridge_df.copy())
        # Only the maximum-height row survives; everything else is flat
        peak_mask = result["height"] >= result["height"].max()
        non_peak = ~peak_mask
        assert (result.loc[non_peak, "ymax"] == result.loc[non_peak, "ymin"]).all()

    def test_integrates_end_to_end(self, raw_df, tmp_path):
        p = ggplot(raw_df, aes("x", "y")) + geom_density_ridges(rel_min_height=0.01)
        p.save(tmp_path / "rel_min_height.png", verbose=False)

    def test_rel_and_abs_min_height_combined(self, ridge_df):
        """When both min_height and rel_min_height are set, the larger wins."""
        ridge_df = ridge_df.copy()
        ridge_df["min_height"] = 0.1  # absolute threshold
        g = geom_ridgeline(rel_min_height=0.5)  # relative threshold = 0.5
        result = g.setup_data(ridge_df)
        threshold = max(0.1, 0.5 * ridge_df["height"].max())
        below = result["height"] < threshold
        assert (result.loc[below, "ymax"] == result.loc[below, "ymin"]).all()


# ── panel_scaling ─────────────────────────────────────────────────────────────


class TestPanelScaling:
    def _compute(self, df, **kwargs):
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

    def test_panel_scaling_true_max_is_one(self, raw_df):
        """Default panel_scaling=True → max ndensity in the panel == 1."""
        result = self._compute(raw_df, panel_scaling=True)
        assert pytest.approx(result["ndensity"].max()) == 1.0

    def test_panel_scaling_false_no_ndensity_in_panel(self, raw_df):
        """panel_scaling=False → compute_panel does not set ndensity."""
        result = self._compute(raw_df, panel_scaling=False)
        assert "ndensity" not in result.columns

    def test_panel_scaling_false_global_normalisation(self, raw_df, tmp_path):
        """panel_scaling=False renders without error (global norm via compute_layer)."""
        p = ggplot(raw_df, aes("x", "y")) + geom_density_ridges(panel_scaling=False)
        p.save(tmp_path / "panel_scaling_false.png", verbose=False)

    def test_panel_scaling_false_across_facets(self, tmp_path):
        """panel_scaling=False makes ridge heights comparable across facets."""
        rng = np.random.default_rng(1)
        df = pd.concat(
            [
                pd.DataFrame({"x": rng.normal(0, 1, 50), "y": "A", "facet": "G1"}),
                pd.DataFrame({"x": rng.normal(0, 1, 200), "y": "A", "facet": "G2"}),
            ],
            ignore_index=True,
        )
        p = (
            ggplot(df, aes("x", "y"))
            + geom_density_ridges(panel_scaling=False)
            + facet_wrap("facet")
        )
        p.save(tmp_path / "panel_scaling_facets.png", verbose=False)


# ── theme_ridges ──────────────────────────────────────────────────────────────


class TestThemeRidges:
    def test_returns_theme_object(self):
        t = theme_ridges()
        assert isinstance(t, theme)

    def test_custom_font_size(self):
        t = theme_ridges(font_size=18)
        assert isinstance(t, theme)

    def test_grid_false(self):
        t = theme_ridges(grid=False)
        assert isinstance(t, theme)

    def test_custom_line_size(self):
        t = theme_ridges(line_size=1.0)
        assert isinstance(t, theme)

    def test_composes_with_plot(self, raw_df, tmp_path):
        p = ggplot(raw_df, aes("x", "y")) + geom_density_ridges() + theme_ridges()
        p.save(tmp_path / "theme_ridges.png", verbose=False)

    def test_composes_with_grid_false(self, raw_df, tmp_path):
        p = (
            ggplot(raw_df, aes("x", "y"))
            + geom_density_ridges()
            + theme_ridges(grid=False)
        )
        p.save(tmp_path / "theme_ridges_no_grid.png", verbose=False)
