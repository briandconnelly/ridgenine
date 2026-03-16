"""Tests for geom_density_ridges_gradient."""

import numpy as np
import pandas as pd
import pytest
from plotnine import aes, ggplot, scale_fill_gradient
from plotnine.mapping.evaluation import after_stat

from ridgenine import geom_density_ridges_gradient, geom_ridgeline


@pytest.fixture
def simple_df():
    rng = np.random.default_rng(42)
    cats = ["A", "B", "C"]
    return pd.concat(
        [
            pd.DataFrame({"x": rng.normal(i, 1, 50), "y": cat})
            for i, cat in enumerate(cats)
        ],
        ignore_index=True,
    )


@pytest.fixture
def ridge_df():
    x = np.linspace(-3, 3, 40)
    frames = [
        pd.DataFrame({"x": x, "y": float(y), "height": np.exp(-0.5 * x**2)})
        for y in [1.0, 2.0, 3.0]
    ]
    return pd.concat(frames, ignore_index=True)


class TestClassAttributes:
    def test_inherits_from_geom_ridgeline(self):
        assert issubclass(geom_density_ridges_gradient, geom_ridgeline)

    def test_default_stat(self):
        assert geom_density_ridges_gradient.DEFAULT_PARAMS["stat"] == "density_ridges"

    def test_default_fill_is_after_stat_x(self):
        fill = geom_density_ridges_gradient.DEFAULT_AES["fill"]
        assert "x" in str(fill)

    def test_default_height_mapping(self):
        height = geom_density_ridges_gradient.DEFAULT_AES["height"]
        assert "ndensity" in str(height)


class TestRendering:
    def test_basic_render(self, simple_df, tmp_path):
        p = (
            ggplot(simple_df, aes("x", "y"))
            + geom_density_ridges_gradient()
            + scale_fill_gradient(low="#440154", high="#fde725")
        )
        p.save(tmp_path / "gradient.png", verbose=False)

    def test_with_scale(self, simple_df, tmp_path):
        p = (
            ggplot(simple_df, aes("x", "y"))
            + geom_density_ridges_gradient(scale=2.0)
            + scale_fill_gradient(low="#440154", high="#fde725")
        )
        p.save(tmp_path / "gradient_scale.png", verbose=False)

    def test_with_alpha(self, simple_df, tmp_path):
        p = (
            ggplot(simple_df, aes("x", "y"))
            + geom_density_ridges_gradient(alpha=0.7)
            + scale_fill_gradient(low="#440154", high="#fde725")
        )
        p.save(tmp_path / "gradient_alpha.png", verbose=False)

    def test_with_trim(self, simple_df, tmp_path):
        p = (
            ggplot(simple_df, aes("x", "y"))
            + geom_density_ridges_gradient(trim=True)
            + scale_fill_gradient(low="#440154", high="#fde725")
        )
        p.save(tmp_path / "gradient_trim.png", verbose=False)

    def test_outline_type_upper(self, simple_df, tmp_path):
        p = (
            ggplot(simple_df, aes("x", "y"))
            + geom_density_ridges_gradient(outline_type="upper")
            + scale_fill_gradient(low="#440154", high="#fde725")
        )
        p.save(tmp_path / "gradient_upper.png", verbose=False)

    def test_outline_type_both(self, simple_df, tmp_path):
        p = (
            ggplot(simple_df, aes("x", "y"))
            + geom_density_ridges_gradient(outline_type="both")
            + scale_fill_gradient(low="#440154", high="#fde725")
        )
        p.save(tmp_path / "gradient_both.png", verbose=False)

    def test_outline_type_full(self, simple_df, tmp_path):
        p = (
            ggplot(simple_df, aes("x", "y"))
            + geom_density_ridges_gradient(outline_type="full")
            + scale_fill_gradient(low="#440154", high="#fde725")
        )
        p.save(tmp_path / "gradient_full.png", verbose=False)

    def test_single_group(self, tmp_path):
        df = pd.DataFrame(
            {
                "x": np.random.default_rng(0).normal(0, 1, 50),
                "y": "A",
            }
        )
        p = (
            ggplot(df, aes("x", "y"))
            + geom_density_ridges_gradient()
            + scale_fill_gradient(low="#440154", high="#fde725")
        )
        p.save(tmp_path / "gradient_single.png", verbose=False)

    def test_quantile_fill(self, simple_df, tmp_path):
        """Map fill to quantile for discrete colour bands."""
        p = ggplot(
            simple_df, aes("x", "y", fill=after_stat("quantile"))
        ) + geom_density_ridges_gradient(quantiles=4)
        p.save(tmp_path / "gradient_quantile.png", verbose=False)
