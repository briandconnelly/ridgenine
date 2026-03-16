from __future__ import annotations

from contextlib import suppress

import numpy as np
import pandas as pd

from plotnine.exceptions import PlotnineError
from plotnine.mapping.evaluation import after_stat
from plotnine.stats.stat import stat
from plotnine.stats.stat_density import compute_density, stat_density


class stat_density_ridges(stat):
    """
    Compute kernel density estimates for ridgeline plots.

    For each group (y-category), runs a KDE on the x values and
    produces a long data frame of density curve points. The ``height``
    aesthetic is mapped to ``ndensity`` by default (density normalised
    to [0, 1] across the whole panel), but can be overridden via
    ``aes(height=after_stat("density"))`` or
    ``aes(height=after_stat("count"))``.

    Parameters
    ----------
    scale : float, default=1.0
        Passed through to ``geom_ridgeline``; controls how tall the
        tallest ridge is relative to the gap between categories.
    kernel : str, default="gaussian"
        Kernel for density estimation (same options as
        ``stat_density``).
    adjust : float, default=1
        Bandwidth multiplier.
    trim : bool, default=False
        Trim density to the data range of each group.
    n : int, default=512
        Number of evaluation points per group.
    bw : str | float, default="nrd0"
        Bandwidth or bandwidth method.
    cut : float, default=3
        Grid extension past the data range, in multiples of ``bw``.
    clip : tuple[float, float], default=(-inf, inf)
        Drop x values outside this range before fitting.
    bounds : tuple[float, float], default=(-inf, inf)
        Domain boundaries for boundary-bias correction.

    See Also
    --------
    ridgenine.geom_density_ridges : The default geom for this stat.
    """

    REQUIRED_AES = {"x", "y"}
    NON_MISSING_AES = {"weight"}
    DEFAULT_AES = {"height": after_stat("ndensity"), "weight": None}
    CREATES = {"height", "density", "ndensity", "scaled", "count", "n"}
    DEFAULT_PARAMS = {
        "geom": "ridgeline",
        "position": "identity",
        "na_rm": False,
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

    def setup_params(self, data: pd.DataFrame) -> None:
        params = self.params
        lookup = {
            "biweight": "biw",
            "cosine": "cos",
            "cosine2": "cos2",
            "epanechnikov": "epa",
            "gaussian": "gau",
            "triangular": "tri",
            "triweight": "triw",
            "uniform": "uni",
        }

        with suppress(KeyError):
            params["kernel"] = lookup[params["kernel"].lower()]

        if params["kernel"] not in lookup.values():
            msg = (
                f"kernel should be one of {list(lookup.keys())}. "
                f"You may use the abbreviations {list(lookup.values())}"
            )
            raise PlotnineError(msg)

    def compute_panel(self, data: pd.DataFrame, scales) -> pd.DataFrame:
        data = super().compute_panel(data, scales)
        if not len(data):
            return data
        max_density = data["density"].max()
        data["ndensity"] = data["density"] / max_density if max_density > 0 else 0.0
        return data

    def compute_group(self, data: pd.DataFrame, scales) -> pd.DataFrame:
        y_value = data["y"].iloc[0]
        weight = data.get("weight")
        if weight is not None:
            weight = np.asarray(weight, dtype=float).copy()

        if self.params["trim"]:
            range_x = data["x"].min(), data["x"].max()
        else:
            range_x = scales.x.dimension()

        dens = compute_density(data["x"], weight, range_x, self.params)

        if not len(dens):
            return dens

        dens["y"] = y_value
        return dens
