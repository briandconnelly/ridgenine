from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from plotnine._utils import resolution
from plotnine.geoms.geom_polygon import geom_polygon
from plotnine.geoms.geom_ribbon import geom_ribbon

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from plotnine.coords.coord import coord
    from plotnine.iapi import panel_view


class geom_ridgeline(geom_ribbon):
    """
    Draw ridgelines — filled density curves stacked on discrete y categories.

    This is the lower-level geom that expects pre-computed ``height`` values.
    For automatic density estimation use ``geom_density_ridges`` instead.

    The ``height`` aesthetic controls how tall each point on the curve is,
    relative to the category's baseline y position. The ``scale`` parameter
    converts that normalised height into data-coordinate units based on the
    spacing between categories.

    Parameters
    ----------
    scale : float, default=1.0
        Multiplier for the ridge height. ``scale=1`` means the tallest
        ridge exactly reaches the next category's baseline. Values > 1
        cause overlap; values < 1 leave gaps.
    outline_type : str, default="upper"
        Which boundary of the filled area to stroke. One of
        ``"upper"``, ``"lower"``, ``"both"``, or ``"full"``.

    See Also
    --------
    ridgenine.geom_density_ridges : High-level geom with automatic KDE.
    ridgenine.stat_density_ridges : Stat that computes heights for ridgelines.
    """

    REQUIRED_AES = {"x", "y", "height"}
    DEFAULT_AES = {
        **geom_ribbon.DEFAULT_AES,
        "color": "#333333",
        "fill": "#808080",
        "min_height": 0,
    }
    DEFAULT_PARAMS = {
        **geom_ribbon.DEFAULT_PARAMS,
        "stat": "identity",
        "position": "identity",
        "na_rm": False,
        "scale": 1.0,
        "outline_type": "upper",
        "rel_min_height": 0,
    }
    draw_legend = staticmethod(geom_polygon.draw_legend)

    def setup_data(self, data: pd.DataFrame) -> pd.DataFrame:
        y_res = resolution(data["y"], False)
        if y_res == 0:
            y_res = 1.0

        scale = self.params["scale"]
        data = data.copy()
        data["ymin"] = data["y"]
        data["ymax"] = data["y"] + data["height"] * scale * y_res

        # Clip ridges below min_height (absolute) to the flat baseline
        min_height = data["min_height"] if "min_height" in data.columns else 0
        # Clip ridges below rel_min_height (relative to panel max) to the baseline
        rel_threshold = self.params["rel_min_height"] * data["height"].max()
        threshold = np.maximum(min_height, rel_threshold)
        mask = data["height"] < threshold
        data.loc[mask, "ymax"] = data.loc[mask, "ymin"]

        return data

    def draw_panel(
        self,
        data: pd.DataFrame,
        panel_params: panel_view,
        coord: coord,
        ax: Axes,
        **params: Any,
    ) -> None:
        # Draw groups from highest y to lowest y so that the bottom-most
        # ridge is painted last and appears in front — matching ggridges behaviour.
        y_order = data.groupby("group")["y"].mean().sort_values(ascending=False).index
        for group in y_order:
            group_data = data[data["group"] == group]
            self.draw_group(group_data, panel_params, coord, ax, self.params)

    def handle_na(self, data: pd.DataFrame) -> pd.DataFrame:
        # Preserve all rows — baseline continuity matters for fill rendering
        return data
