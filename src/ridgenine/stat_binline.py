from __future__ import annotations

import numpy as np
import pandas as pd
from plotnine.mapping.evaluation import after_stat
from plotnine.stats.stat import stat


class stat_binline(stat):
    """
    Compute binned heights for histogram-style ridgeline plots.

    For each group (y-category), bins the x values into a histogram and
    produces a step-function data frame suitable for ``geom_ridgeline``.
    This is the discrete alternative to ``stat_density_ridges``.

    Parameters
    ----------
    bins : int, default=30
        Number of bins.
    binwidth : float or None, default=None
        Width of each bin. Overrides ``bins`` when set.
    center : float or None, default=None
        Center of one of the bins.
    boundary : float or None, default=None
        Boundary between two bins.
    breaks : list[float] or None, default=None
        Explicit bin edges. Overrides ``bins`` and ``binwidth``.
    draw_baseline : bool, default=True
        If ``True``, include zero-height points at bin edges so the
        step function returns to the baseline between groups.
    pad : bool, default=True
        If ``True``, add zero-height points at the extremes so ridges
        start and end at the baseline.

    See Also
    --------
    ridgenine.stat_density_ridges : KDE-based alternative.
    ridgenine.geom_ridgeline : The default geom for this stat.
    """

    REQUIRED_AES = {"x", "y"}
    NON_MISSING_AES = {"weight"}
    DEFAULT_AES = {"height": after_stat("ndensity"), "weight": None}
    CREATES = {"height", "density", "ndensity", "count", "ncount"}
    DEFAULT_PARAMS = {
        "geom": "ridgeline",
        "position": "identity",
        "na_rm": False,
        "bins": 30,
        "binwidth": None,
        "center": None,
        "boundary": None,
        "breaks": None,
        "draw_baseline": True,
        "pad": True,
    }

    def compute_group(self, data: pd.DataFrame, scales) -> pd.DataFrame:
        y_value = data["y"].iloc[0]
        x = data["x"].values
        weight = data.get("weight")
        if weight is not None:
            weight = np.asarray(weight, dtype=float)

        edges = self._compute_edges(x, scales)
        counts, _ = np.histogram(x, bins=edges, weights=weight)

        n_obs = len(x) if weight is None else weight.sum()
        widths = np.diff(edges)
        density = counts / (n_obs * widths) if n_obs > 0 else counts * 0.0

        # Build step-function output: two points per bin (left and right edge)
        xs = []
        heights = []
        for i in range(len(counts)):
            xs.extend([edges[i], edges[i + 1]])
            heights.extend([density[i], density[i]])

        xs = np.array(xs)
        heights = np.array(heights)
        counts_expanded = np.repeat(counts, 2)

        # Pad with zero-height points at the extremes
        if self.params["pad"]:
            pad_x = np.array([edges[0], edges[-1]])
            pad_h = np.array([0.0, 0.0])
            pad_c = np.array([0.0, 0.0])
            xs = np.concatenate([pad_x[:1], xs, pad_x[1:]])
            heights = np.concatenate([pad_h[:1], heights, pad_h[1:]])
            counts_expanded = np.concatenate([pad_c[:1], counts_expanded, pad_c[1:]])

        max_density = heights.max() if len(heights) else 1.0
        max_count = counts_expanded.max() if len(counts_expanded) else 1.0

        result = pd.DataFrame(
            {
                "x": xs,
                "y": y_value,
                "density": heights,
                "ndensity": heights / max_density if max_density > 0 else 0.0,
                "count": counts_expanded,
                "ncount": counts_expanded / max_count if max_count > 0 else 0.0,
            }
        )
        return result

    def _compute_edges(self, x: np.ndarray, scales) -> np.ndarray:
        """Determine histogram bin edges."""
        if self.params["breaks"] is not None:
            return np.asarray(self.params["breaks"], dtype=float)

        range_x = scales.x.dimension()

        if self.params["binwidth"] is not None:
            binwidth = self.params["binwidth"]
            if self.params["boundary"] is not None:
                shift = (range_x[0] - self.params["boundary"]) % binwidth
                start = range_x[0] - shift
            elif self.params["center"] is not None:
                shift = (range_x[0] - self.params["center"]) % binwidth
                start = range_x[0] - shift - binwidth / 2
            else:
                start = range_x[0]
            edges = np.arange(start, range_x[1] + binwidth, binwidth)
            # Ensure we cover the full range
            if edges[-1] < range_x[1]:
                edges = np.append(edges, edges[-1] + binwidth)
        else:
            edges = np.linspace(range_x[0], range_x[1], self.params["bins"] + 1)

        return edges
