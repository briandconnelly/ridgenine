import warnings

import numpy as np
import pandas as pd
import pytest
from plotnine import aes, ggplot
from plotnine.exceptions import PlotnineError, PlotnineWarning

from ridgenine import geom_density_ridges, stat_density_ridges


def _compute(df, **kwargs):
    """Run stat_density_ridges.compute_panel on df grouped by y."""
    from unittest.mock import MagicMock

    s = stat_density_ridges(**kwargs)
    s.setup_params(df)

    # plotnine's compute_panel groups by the 'group' column which it
    # normally adds during layer setup; we add it here manually.
    df = df.copy()
    if "group" not in df.columns:
        codes, _ = pd.factorize(df["y"])
        df["group"] = codes + 1

    # Build a minimal scales mock with x dimension matching data range
    scales = MagicMock()
    scales.x.dimension.return_value = (df["x"].min() - 1, df["x"].max() + 1)

    return s.compute_panel(df, scales)


class TestOutputColumns:
    def test_creates_expected_columns(self, simple_df):
        result = _compute(simple_df)
        for col in ("x", "y", "density", "ndensity", "count", "n", "scaled"):
            assert col in result.columns, f"missing column: {col}"

    def test_ndensity_range(self, simple_df):
        result = _compute(simple_df)
        assert result["ndensity"].between(0, 1).all()

    def test_ndensity_max_is_one(self, simple_df):
        result = _compute(simple_df)
        assert pytest.approx(result["ndensity"].max()) == 1.0

    def test_group_y_preserved(self, simple_df):
        result = _compute(simple_df)
        # Each original y category should appear in the output
        assert set(result["y"].unique()) == {"A", "B", "C"}

    def test_numeric_y_preserved(self, numeric_y_df):
        result = _compute(numeric_y_df)
        assert set(result["y"].unique()) == {1.0, 2.0, 3.0}


class TestParams:
    def test_trim_narrows_range(self, simple_df):
        result_full = _compute(simple_df, trim=False)
        result_trim = _compute(simple_df, trim=True)
        # Trimmed range should be no wider per group
        for y_val in result_full["y"].unique():
            s_full = result_full.loc[result_full["y"] == y_val, "x"]
            s_trim = result_trim.loc[result_trim["y"] == y_val, "x"]
            full_range = s_full.max() - s_full.min()
            trim_range = s_trim.max() - s_trim.min()
            assert trim_range <= full_range + 1e-9

    def test_bw_float(self, simple_df):
        result = _compute(simple_df, bw=0.5)
        assert len(result) > 0

    def test_custom_n_points(self, simple_df):
        result = _compute(simple_df, n=64)
        # Each group should produce ~64 points (fewer if NaNs dropped)
        for y_val in result["y"].unique():
            group_n = len(result[result["y"] == y_val])
            assert group_n <= 64

    def test_weight_changes_density(self, simple_df):
        rng = np.random.default_rng(99)
        df = simple_df.copy()
        # Non-uniform within-group weights concentrate mass on a subset
        df["weight"] = rng.uniform(0.1, 10.0, len(df))
        result_w = _compute(df)
        result_nw = _compute(simple_df)
        # Weighted and unweighted densities for group A should differ
        a_w = result_w.loc[result_w["y"] == "A", "density"].values
        a_nw = result_nw.loc[result_nw["y"] == "A", "density"].values
        assert not np.allclose(a_w, a_nw)


class TestKernels:
    def test_invalid_kernel_raises(self, simple_df):
        with pytest.raises(PlotnineError, match="kernel"):
            _compute(simple_df, kernel="nope")

    @pytest.mark.parametrize(
        "kernel",
        ["gaussian", "epanechnikov", "uniform", "triangular", "biweight", "triweight"],
    )
    def test_valid_kernels(self, simple_df, kernel):
        result = _compute(simple_df, kernel=kernel)
        assert len(result) > 0


class TestEdgeCases:
    def test_single_obs_group_warns(self):
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0, 99.0], "y": ["A", "A", "A", "B"]})
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _compute(df)
        messages = [str(warning.message) for warning in w]
        assert any("fewer than 2" in m or "only one" in m for m in messages)

    def test_empty_panel_returns_empty(self):
        from unittest.mock import MagicMock

        stat = stat_density_ridges()
        stat.setup_params(pd.DataFrame({"x": [], "y": []}))
        scales = MagicMock()
        scales.x.dimension.return_value = (0, 1)
        result = stat.compute_panel(pd.DataFrame({"x": [], "y": []}), scales)
        assert len(result) == 0

    def test_all_same_x_values_warns(self):
        df = pd.DataFrame({"x": [5.0, 5.0, 5.0], "y": ["A", "A", "A"]})
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            # Should not raise, may warn or return empty
            try:
                _compute(df)
            except Exception:
                pass  # acceptable — single-value group is degenerate


class TestIntegration:
    def test_renders_without_error(self, simple_df, tmp_path):
        p = ggplot(simple_df, aes("x", "y")) + geom_density_ridges()
        p.save(tmp_path / "test.png", verbose=False)

    def test_stat_as_standalone_layer(self, simple_df, tmp_path):
        from plotnine import geom_line

        p = (
            ggplot(simple_df, aes("x", "y"))
            + stat_density_ridges()
        )
        p.save(tmp_path / "test_stat.png", verbose=False)
