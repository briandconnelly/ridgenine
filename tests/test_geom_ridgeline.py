from unittest.mock import call, patch

import numpy as np
import pandas as pd
import pytest
from plotnine import aes, ggplot
from plotnine.mapping.evaluation import after_stat

from ridgenine import geom_ridgeline


def _make_ridge_df(n=20, y_vals=None):
    """Minimal data frame suitable for geom_ridgeline."""
    if y_vals is None:
        y_vals = [1.0, 2.0, 3.0]
    rng = np.random.default_rng(7)
    frames = []
    for y in y_vals:
        x = np.linspace(-3, 3, n)
        height = np.exp(-0.5 * x**2)  # gaussian shape
        frames.append(pd.DataFrame({"x": x, "y": y, "height": height}))
    return pd.concat(frames, ignore_index=True)


class TestSetupData:
    def test_ymin_equals_y(self):
        df = _make_ridge_df()
        g = geom_ridgeline()
        result = g.setup_data(df)
        pd.testing.assert_series_equal(result["ymin"], result["y"], check_names=False)

    def test_ymax_offset(self):
        df = _make_ridge_df(y_vals=[1.0, 2.0])
        g = geom_ridgeline(scale=1.0)
        result = g.setup_data(df)
        # y_res = 1.0 (spacing between 1 and 2), scale=1
        expected_ymax = result["y"] + result["height"] * 1.0 * 1.0
        pd.testing.assert_series_equal(result["ymax"], expected_ymax, check_names=False)

    def test_scale_doubles_height(self):
        df = _make_ridge_df(y_vals=[1.0, 2.0])
        g1 = geom_ridgeline(scale=1.0)
        g2 = geom_ridgeline(scale=2.0)
        r1 = g1.setup_data(df)
        r2 = g2.setup_data(df)
        # heights (ymax - ymin) should be doubled
        h1 = (r1["ymax"] - r1["ymin"]).values
        h2 = (r2["ymax"] - r2["ymin"]).values
        np.testing.assert_allclose(h2, h1 * 2)

    def test_min_height_clips_low_values(self):
        df = _make_ridge_df(y_vals=[1.0, 2.0])
        df["min_height"] = 0.5
        g = geom_ridgeline()
        result = g.setup_data(df)
        # Where height < 0.5, ymax should equal ymin (flat)
        below = result["height"] < 0.5
        assert (result.loc[below, "ymax"] == result.loc[below, "ymin"]).all()
        # Where height >= 0.5, ymax should be above ymin
        above = ~below
        assert (result.loc[above, "ymax"] >= result.loc[above, "ymin"]).all()

    def test_resolution_scales_correctly(self):
        # y spacing of 2 → y_res=2, same scale should give 2× ymax offset
        df_res1 = _make_ridge_df(y_vals=[1.0, 2.0])
        df_res2 = _make_ridge_df(y_vals=[0.0, 2.0])  # spacing=2
        g = geom_ridgeline(scale=1.0)
        r1 = g.setup_data(df_res1)
        r2 = g.setup_data(df_res2)
        h1 = (r1["ymax"] - r1["ymin"]).values
        h2 = (r2["ymax"] - r2["ymin"]).values
        np.testing.assert_allclose(h2, h1 * 2)

    def test_single_category_resolution_fallback(self):
        """When resolution() returns 0 (e.g. mocked), height falls back to 1."""
        from unittest.mock import patch

        df = _make_ridge_df(y_vals=[5.0])
        g = geom_ridgeline(scale=1.0)
        with patch("ridgenine.geom_ridgeline.resolution", return_value=0):
            result = g.setup_data(df)
        # fallback y_res=1.0 → ymax should still be above ymin for positive heights
        assert (result["ymax"] >= result["ymin"]).all()

    def test_setup_data_does_not_mutate_input(self):
        df = _make_ridge_df()
        original_cols = set(df.columns)
        g = geom_ridgeline()
        g.setup_data(df)
        assert set(df.columns) == original_cols


class TestDrawOrder:
    def test_lowest_y_group_drawn_last(self):
        """draw_panel iterates groups from highest y to lowest y."""
        from unittest.mock import MagicMock

        df = _make_ridge_df(y_vals=[1.0, 2.0, 3.0])
        df["group"] = df["y"].map({1.0: 1, 2.0: 2, 3.0: 3})
        df = geom_ridgeline().setup_data(df)

        draw_order = []

        # Stub out draw_group — just record which y value each call received
        def recording(data, panel_params, coord, ax, params):
            draw_order.append(round(data["y"].iloc[0], 1))

        g = geom_ridgeline()
        with patch.object(geom_ridgeline, "draw_group", staticmethod(recording)):
            g.draw_panel(df, MagicMock(), MagicMock(), MagicMock())

        # Highest y (3.0) first, lowest y (1.0) last (drawn on top)
        assert draw_order == [3.0, 2.0, 1.0]


class TestHandleNa:
    def test_handle_na_preserves_rows(self):
        df = _make_ridge_df()
        df.loc[0, "x"] = np.nan
        g = geom_ridgeline()
        result = g.handle_na(df)
        assert len(result) == len(df)


class TestIntegration:
    def test_basic_render(self, tmp_path):
        df = _make_ridge_df()
        p = ggplot(df, aes("x", "y", height="height")) + geom_ridgeline()
        p.save(tmp_path / "ridgeline.png", verbose=False)

    def test_single_category(self, tmp_path):
        df = _make_ridge_df(y_vals=[1.0])
        p = ggplot(df, aes("x", "y", height="height")) + geom_ridgeline()
        p.save(tmp_path / "ridgeline_single.png", verbose=False)

    def test_scale_param(self, tmp_path):
        df = _make_ridge_df()
        p = ggplot(df, aes("x", "y", height="height")) + geom_ridgeline(scale=2.0)
        p.save(tmp_path / "ridgeline_scale.png", verbose=False)

    def test_fill_aesthetic(self, tmp_path):
        df = _make_ridge_df()
        p = (
            ggplot(df, aes("x", "y", height="height"))
            + geom_ridgeline(fill="#4C72B0", alpha=0.7)
        )
        p.save(tmp_path / "ridgeline_fill.png", verbose=False)

    def test_outline_type_both(self, tmp_path):
        df = _make_ridge_df()
        p = (
            ggplot(df, aes("x", "y", height="height"))
            + geom_ridgeline(outline_type="both")
        )
        p.save(tmp_path / "ridgeline_both.png", verbose=False)

    def test_outline_type_full(self, tmp_path):
        df = _make_ridge_df()
        p = (
            ggplot(df, aes("x", "y", height="height"))
            + geom_ridgeline(outline_type="full")
        )
        p.save(tmp_path / "ridgeline_full.png", verbose=False)
