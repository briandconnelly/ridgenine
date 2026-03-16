from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib.cm as cm
import numpy as np
import pandas as pd
from plotnine._utils import to_rgba
from plotnine.geoms.geom_path import geom_path
from plotnine.geoms.geom_polygon import geom_polygon
from plotnine.mapping.evaluation import after_stat, stage

from .geom_ridgeline import geom_ridgeline

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from plotnine.coords.coord import coord
    from plotnine.iapi import panel_view


class geom_density_ridges_gradient(geom_ridgeline):
    """
    Ridgeline plot with gradient fills along the x-axis.

    Like ``geom_density_ridges``, but allows the fill colour to vary
    continuously along each ridge. By default, fill is mapped to x
    position, producing a smooth colour gradient. Map fill to
    ``after_stat("quantile")`` for quantile-shaded ridges.

    The ridge is rendered as a series of thin vertical strips, each
    receiving its own fill colour from the mapped aesthetic.

    Parameters
    ----------
    scale : float, default=1.0
        Controls how much ridges overlap. ``1.0`` means the tallest ridge
        exactly fills the space to the next category; values > 1 cause
        overlap, values < 1 leave gaps.
    rel_min_height : float, default=0
        Clip density tails below this fraction of the panel-wide maximum
        height to the baseline.
    panel_scaling : bool, default=True
        If ``True``, normalise heights independently per panel.
        If ``False``, normalise globally.
    kernel : str, default="gaussian"
        KDE kernel.
    adjust : float, default=1
        Bandwidth multiplier.
    trim : bool, default=False
        Trim density to the data range of each group.
    n : int, default=512
        Number of density evaluation points per group.
    bw : str | float, default="nrd0"
        Bandwidth or bandwidth method.

    Examples
    --------
    .. plot::
        :context: close-figs

        import numpy as np
        import pandas as pd
        from plotnine import ggplot, aes, scale_fill_viridis_c
        from ridgenine import geom_density_ridges_gradient

        rng = np.random.default_rng(42)
        cats = ["A", "B", "C", "D"]
        df = pd.concat([
            pd.DataFrame({"x": rng.normal(i, 1, 200), "category": c})
            for i, c in enumerate(cats)
        ])

        (
            ggplot(df, aes("x", "category"))
            + geom_density_ridges_gradient(scale=1.5)
            + scale_fill_viridis_c()
        )

    See Also
    --------
    ridgenine.geom_density_ridges : Non-gradient version with uniform fill.
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
    }
    DEFAULT_AES = {
        **geom_ridgeline.DEFAULT_AES,
        "height": after_stat("ndensity"),
        "fill": after_stat("x"),
    }
    NON_MISSING_AES = frozenset()
    draw_legend = staticmethod(geom_polygon.draw_legend)

    def draw_panel(
        self,
        data: pd.DataFrame,
        panel_params: panel_view,
        coord: coord,
        ax: Axes,
        **params: Any,
    ) -> None:
        y_order = data.groupby("group")["y"].mean().sort_values(ascending=False).index
        for group in y_order:
            group_data = data[data["group"] == group].copy()
            group_data.reset_index(drop=True, inplace=True)
            self._draw_gradient_group(group_data, panel_params, coord, ax, self.params)

    @staticmethod
    def _draw_gradient_group(
        data: pd.DataFrame,
        panel_params: panel_view,
        coord: coord,
        ax: Axes,
        params: dict[str, Any],
    ) -> None:
        from matplotlib.collections import PolyCollection

        data = coord.transform(data, panel_params, munch=True)
        data = data.sort_values("x", kind="mergesort").reset_index(drop=True)

        n = len(data)
        if n < 2:
            return

        x = data["x"].values
        ymin = data["ymin"].values
        ymax = data["ymax"].values
        # Build one trapezoid per consecutive pair of points
        verts = []
        strip_indices = []
        for i in range(n - 1):
            verts.append(
                [
                    (x[i], ymin[i]),
                    (x[i], ymax[i]),
                    (x[i + 1], ymax[i + 1]),
                    (x[i + 1], ymin[i + 1]),
                ]
            )
            strip_indices.append(i)

        # Use the fill colour at each strip's left edge.
        # If fill contains unresolved after_stat objects (DEFAULT_AES wasn't
        # mapped through a scale), fall back to a viridis gradient over x.
        fill_col = data["fill"]
        if len(fill_col) and isinstance(fill_col.iloc[0], stage):
            x_vals = data["x"].values
            x_range = x_vals.max() - x_vals.min()
            normed = (x_vals - x_vals.min()) / (x_range if x_range > 0 else 1.0)
            alpha_val = data["alpha"].iloc[0]
            cmap = cm.get_cmap("viridis")
            fill_colors = [(*cmap(v)[:3], alpha_val) for v in normed]
        else:
            fill_colors = to_rgba(data["fill"], data["alpha"])
        strip_fills = [fill_colors[i] for i in strip_indices]

        col = PolyCollection(
            verts,
            facecolors=strip_fills,
            edgecolors="none",
            linewidths=0,
            zorder=params["zorder"],
            rasterized=params["raster"],
        )
        ax.add_collection(col)

        # Draw the outline on top
        outline_type = params.get("outline_type", "upper")
        data_outline = data.copy()
        data_outline["alpha"] = 1

        if outline_type == "full":
            # Closed polygon outline
            xs = np.concatenate([x, x[::-1]])
            ys = np.concatenate([ymax, ymin[::-1]])
            outline_data = data_outline.iloc[[0]].copy()
            outline_data = pd.DataFrame(
                {
                    c: outline_data[c].repeat(len(xs)).values
                    for c in outline_data.columns
                }
            )
            outline_data["x"] = xs
            outline_data["y"] = ys
            outline_data.reset_index(drop=True, inplace=True)
            geom_path.draw_group(outline_data, panel_params, coord, ax, params)
        else:
            if outline_type in ("upper", "both"):
                upper_data = data_outline.assign(y=data_outline["ymax"])
                geom_path.draw_group(upper_data, panel_params, coord, ax, params)
            if outline_type in ("lower", "both"):
                lower_data = data_outline.assign(y=data_outline["ymin"])
                geom_path.draw_group(lower_data, panel_params, coord, ax, params)
