from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from plotnine.mapping.evaluation import after_stat

from .geom_ridgeline import geom_ridgeline

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from plotnine.coords.coord import coord
    from plotnine.iapi import panel_view


class geom_density_ridges(geom_ridgeline):
    """
    Ridgeline plot with automatic kernel density estimation.

    Computes a KDE for each y-category and draws it as a filled ridge.
    A direct analogue of ``ggridges::geom_density_ridges`` for plotnine.

    Parameters
    ----------
    scale : float, default=1.0
        Controls how much ridges overlap. ``1.0`` means the tallest ridge
        exactly fills the space to the next category; values > 1 cause
        overlap, values < 1 leave gaps.
    rel_min_height : float, default=0
        Clip density tails below this fraction of the panel-wide maximum
        height to the baseline. e.g. ``rel_min_height=0.01`` removes the
        bottom 1% of each ridge's tails.
    panel_scaling : bool, default=True
        If ``True`` (default), normalise heights independently per panel
        so each panel's tallest ridge reaches ``scale``. If ``False``,
        normalise globally so ridge heights are comparable across facets.
    quantile_lines : bool, default=False
        If ``True``, draw vertical lines at quantile boundaries within
        each ridge. Set ``quantiles`` to control the cut points.
    quantiles : int or list[float], optional
        Quantile specification. An integer *k* splits each ridge into *k*
        equal-probability bands. A list of floats (e.g. ``[0.25, 0.5, 0.75]``)
        specifies explicit cut points. Defaults to ``[0.25, 0.5, 0.75]``
        when ``quantile_lines=True``.
    jittered_points : bool, default=False
        If ``True``, draw the raw data points jittered within each
        ridge envelope.
    point_shape : str, default="o"
        Marker shape for jittered points.
    point_size : float, default=0.5
        Size of jittered points.
    point_alpha : float, default=1.0
        Opacity of jittered points.
    point_color : str or None, default=None
        Colour of jittered points. If ``None``, uses the ridge outline
        colour.
    kernel : str, default="gaussian"
        KDE kernel. Same options as ``stat_density``.
    adjust : float, default=1
        Bandwidth multiplier.
    trim : bool, default=False
        Trim density to the data range of each group.
    n : int, default=512
        Number of density evaluation points per group.
    bw : str | float, default="nrd0"
        Bandwidth or bandwidth method.
    cut : float, default=3
        Grid extension past data range in multiples of ``bw``.
    clip : tuple[float, float], default=(-inf, inf)
        Drop x values outside this range before fitting.
    bounds : tuple[float, float], default=(-inf, inf)
        Domain boundaries for boundary-bias correction.

    Examples
    --------
    .. plot::
        :context: close-figs

        import numpy as np
        import pandas as pd
        from plotnine import ggplot, aes, theme_classic
        from ridgenine import geom_density_ridges

        rng = np.random.default_rng(42)
        cats = ["A", "B", "C", "D"]
        df = pd.concat([
            pd.DataFrame({"x": rng.normal(i, 1, 200), "category": c})
            for i, c in enumerate(cats)
        ])

        (
            ggplot(df, aes("x", "category"))
            + geom_density_ridges(scale=1.5, alpha=0.7)
            + theme_classic()
        )

    See Also
    --------
    ridgenine.geom_ridgeline : Lower-level geom for pre-computed heights.
    ridgenine.geom_density_ridges_gradient : Gradient-filled variant.
    ridgenine.stat_density_ridges : The default stat for this geom.
    """

    DEFAULT_PARAMS = {
        **geom_ridgeline.DEFAULT_PARAMS,
        "stat": "density_ridges",
        "panel_scaling": True,
        "kernel": "gaussian",
        "adjust": 1,
        "trim": False,
        "n": 512,
        "gridsize": None,
        "bw": "nrd0",
        "cut": 3,
        "clip": (-np.inf, np.inf),
        "bounds": (-np.inf, np.inf),
        "quantile_lines": False,
        "quantiles": None,
        "jittered_points": False,
        "point_shape": "o",
        "point_size": 0.5,
        "point_alpha": 1.0,
        "point_color": None,
        "point_seed": 42,
    }
    DEFAULT_AES = {
        **geom_ridgeline.DEFAULT_AES,
        "height": after_stat("ndensity"),
    }

    def setup_params(self, data: pd.DataFrame) -> None:
        super().setup_params(data)
        # When quantile_lines is True, ensure quantiles are set
        if self.params.get("quantile_lines") and self.params.get("quantiles") is None:
            self.params["quantiles"] = [0.25, 0.5, 0.75]

    def draw_panel(
        self,
        data: pd.DataFrame,
        panel_params: panel_view,
        coord: coord,
        ax: Axes,
    ) -> None:
        # Draw the ridges (bottom-to-top z-order)
        super().draw_panel(data, panel_params, coord, ax)

        # Draw quantile lines if requested
        if self.params.get("quantile_lines") and "quantile" in data.columns:
            self._draw_quantile_lines(data, panel_params, coord, ax)

        # Draw jittered points if stat stashed them in params
        jitter_data = self.params.get("_jitter_data")
        if self.params.get("jittered_points") and jitter_data:
            point_data = pd.concat(jitter_data, ignore_index=True)
            self._draw_jittered_points(point_data, data, panel_params, coord, ax)
            # Clear after drawing to avoid double-drawing across panels
            self.params["_jitter_data"] = None

    def _draw_jittered_points(
        self,
        point_data: pd.DataFrame,
        ridge_data: pd.DataFrame,
        panel_params: panel_view,
        coord: coord,
        ax: Axes,
    ) -> None:
        """Draw jittered data points within the ridge envelopes."""
        from plotnine._utils import resolution, to_rgba

        point_data = point_data.copy()

        # Compute the y-offset for each point using the stored jitter and
        # the ridge height at that x position.
        # Use ymin (numeric baseline) for resolution, not y (may be categorical)
        y_res = resolution(ridge_data["ymin"], False)
        if y_res == 0:
            y_res = 1.0
        scale = self.params["scale"]

        # Build a mapping from group_id to numeric baseline (ymin) from ridge data
        group_baselines = ridge_data.groupby("group")["ymin"].first().to_dict()

        for group_id in point_data["group"].unique():
            mask = point_data["group"] == group_id
            pts = point_data.loc[mask]
            ridges = ridge_data[ridge_data["group"] == group_id].sort_values("x")
            if not len(ridges):
                continue

            baseline = group_baselines.get(group_id, 0.0)

            # Interpolate density height at each point's x
            height_at_x = np.interp(
                pts["x"].values,
                ridges["x"].values,
                ridges["height"].values,
            )
            jitter = (
                pts["point_jitter"].values if "point_jitter" in pts.columns else 0.5
            )
            y_offset = height_at_x * scale * y_res * jitter
            point_data.loc[mask, "y"] = baseline + y_offset

        # Transform and draw
        draw_data = point_data[["x", "y", "group"]].copy()
        draw_data["color"] = self.params.get("point_color") or point_data.get(
            "color", "#333333"
        )
        draw_data["alpha"] = self.params.get("point_alpha", 1.0)
        draw_data["size"] = self.params.get("point_size", 0.5)
        draw_data["shape"] = self.params.get("point_shape", "o")
        draw_data["stroke"] = 0.3

        draw_data = coord.transform(draw_data, panel_params)

        color = to_rgba(draw_data["color"], draw_data["alpha"])
        size = ((draw_data["size"] + draw_data["stroke"]) ** 2) * np.pi

        ax.scatter(
            x=draw_data["x"],
            y=draw_data["y"],
            s=size,
            facecolor=color,
            edgecolor="none",
            marker=draw_data["shape"].iloc[0],
            zorder=self.params.get("zorder", 1) + 1,
        )

    def _draw_quantile_lines(
        self,
        data: pd.DataFrame,
        panel_params: panel_view,
        coord: coord,
        ax: Axes,
    ) -> None:
        """Draw vertical lines at quantile boundaries within each ridge."""
        from plotnine._utils import SIZE_FACTOR

        for _, group_data in data.groupby("group"):
            group_data = group_data.sort_values("x").reset_index(drop=True)
            quantile_col = group_data["quantile"]
            boundaries = group_data.index[
                quantile_col.diff().ne(0) & (quantile_col.index > 0)
            ]

            for idx in boundaries:
                row = group_data.iloc[idx]
                line_data = pd.DataFrame(
                    {
                        "x": [row["x"], row["x"]],
                        "y": [row["ymin"], row["ymax"]],
                        "color": [group_data["color"].iloc[0]] * 2,
                        "size": [group_data["size"].iloc[0]] * 2,
                        "linetype": [group_data["linetype"].iloc[0]] * 2,
                        "alpha": [1.0, 1.0],
                        "group": [0, 0],
                    }
                )
                line_data = coord.transform(line_data, panel_params)
                linewidth = line_data["size"].iloc[0] * SIZE_FACTOR
                ax.plot(
                    line_data["x"],
                    line_data["y"],
                    color=line_data["color"].iloc[0],
                    linewidth=linewidth,
                    linestyle=line_data["linetype"].iloc[0],
                    zorder=self.params.get("zorder", 1) + 0.5,
                )
