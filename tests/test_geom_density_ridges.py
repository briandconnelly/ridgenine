import numpy as np
import pandas as pd
import pytest
from plotnine import aes, coord_flip, facet_wrap, ggplot
from plotnine.mapping.evaluation import after_stat

from ridgenine import geom_density_ridges, geom_ridgeline, stat_density_ridges


class TestClassAttributes:
    def test_default_stat_is_density_ridges(self):
        assert geom_density_ridges.DEFAULT_PARAMS["stat"] == "density_ridges"

    def test_default_height_mapping(self):
        # height should default to after_stat("ndensity")
        height_default = geom_density_ridges.DEFAULT_AES["height"]
        assert "ndensity" in str(height_default)

    def test_inherits_from_geom_ridgeline(self):
        assert issubclass(geom_density_ridges, geom_ridgeline)


class TestBasicRendering:
    def test_string_y_categories(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges()
        p.save(tmp_path / "string_y.png", verbose=False)

    def test_numeric_y(self, numeric_y_df, tmp_path):
        p = ggplot(numeric_y_df, aes("x", "y")) + geom_density_ridges()
        p.save(tmp_path / "numeric_y.png", verbose=False)

    def test_single_group(self, tmp_path):
        df = pd.DataFrame({"x": np.random.default_rng(0).normal(0, 1, 50), "y": "A"})
        p = ggplot(df, aes("x", "y")) + geom_density_ridges()
        p.save(tmp_path / "single_group.png", verbose=False)

    def test_two_obs_minimum(self, tmp_path):
        df = pd.DataFrame({"x": [1.0, 2.0], "y": ["A", "A"]})
        p = ggplot(df, aes("x", "y")) + geom_density_ridges(bw=0.5)
        p.save(tmp_path / "two_obs.png", verbose=False)


class TestScaleParam:
    def test_scale_overlap(self, simple_df, tmp_path):
        """scale=3 produces ridges that visually overlap (ymax > next y)."""
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(scale=3.0)
        p.save(tmp_path / "overlap.png", verbose=False)

    def test_scale_gap(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(scale=0.3)
        p.save(tmp_path / "gap.png", verbose=False)


class TestKdeParams:
    def test_epanechnikov_kernel(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(kernel="epanechnikov")
        p.save(tmp_path / "epa.png", verbose=False)

    def test_trim_param(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(trim=True)
        p.save(tmp_path / "trim.png", verbose=False)

    def test_bandwidth_float(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(bw=0.5)
        p.save(tmp_path / "bw_float.png", verbose=False)

    def test_n_param(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(n=64)
        p.save(tmp_path / "n64.png", verbose=False)


class TestAesthetics:
    def test_fill_mapped(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y", fill="y")) + geom_density_ridges(alpha=0.7)
        p.save(tmp_path / "fill_mapped.png", verbose=False)

    def test_alpha_aesthetic(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(alpha=0.4)
        p.save(tmp_path / "alpha.png", verbose=False)

    def test_height_density_mapping(self, simple_df, tmp_path):
        p = (
            ggplot(simple_df, aes("x", "y", height=after_stat("density")))
            + geom_density_ridges()
        )
        p.save(tmp_path / "height_density.png", verbose=False)

    def test_height_count_mapping(self, simple_df, tmp_path):
        p = (
            ggplot(simple_df, aes("x", "y", height=after_stat("count")))
            + geom_density_ridges()
        )
        p.save(tmp_path / "height_count.png", verbose=False)

    def test_outline_type_upper(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(outline_type="upper")
        p.save(tmp_path / "outline_upper.png", verbose=False)

    def test_outline_type_both(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(outline_type="both")
        p.save(tmp_path / "outline_both.png", verbose=False)

    def test_outline_type_full(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges(outline_type="full")
        p.save(tmp_path / "outline_full.png", verbose=False)


class TestComposability:
    def test_facet_wrap(self, tmp_path):
        rng = np.random.default_rng(5)
        df = pd.concat([
            pd.DataFrame({"x": rng.normal(i, 1, 40), "y": cat, "group": grp})
            for i, cat in enumerate(["A", "B", "C"])
            for grp in ["G1", "G2"]
        ], ignore_index=True)
        p = (
            ggplot(df, aes("x", "y"))
            + geom_density_ridges()
            + facet_wrap("group")
        )
        p.save(tmp_path / "facet.png", verbose=False)

    def test_coord_flip(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges() + coord_flip()
        p.save(tmp_path / "coord_flip.png", verbose=False)

    def test_stat_separately_usable(self, simple_df, tmp_path):
        """stat_density_ridges can be used on its own (e.g. with geom_ridgeline)."""
        p = (
            ggplot(simple_df, aes("x", "y"))
            + geom_ridgeline(stat="density_ridges")
        )
        p.save(tmp_path / "stat_separate.png", verbose=False)
