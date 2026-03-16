from __future__ import annotations

from contextlib import suppress

import numpy as np
import pandas as pd
from plotnine.exceptions import PlotnineError
from plotnine.mapping.evaluation import after_stat
from plotnine.stats.stat import stat
from plotnine.stats.stat_density import compute_density


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
    CREATES = {
        "height",
        "density",
        "ndensity",
        "scaled",
        "count",
        "n",
        "quantile",
        "datatype",
    }
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
        "panel_scaling": True,
        "quantiles": None,
        "quantile_lines": False,
        "jittered_points": False,
        "point_seed": 42,
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
        if self.params["panel_scaling"]:
            # Normalise density to [0, 1] within this panel
            max_d = data["density"].max()
            data["ndensity"] = data["density"] / max_d if max_d > 0 else 0.0
        return data

    def compute_layer(self, data: pd.DataFrame, layout) -> pd.DataFrame:
        data = super().compute_layer(data, layout)
        if not len(data) or self.params["panel_scaling"]:
            return data
        # panel_scaling=False: normalise globally so ridges are comparable
        # across facets — super().compute_layer already ran compute_panel for
        # each panel but skipped ndensity; we compute it here on the combined
        # output.
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

        # Compute quantile assignments
        quantiles = self.params.get("quantiles")
        if quantiles is not None:
            dens = _assign_quantiles(dens, data["x"], weight, quantiles)

        # Stash raw observations for jittered points (accessed by the geom
        # via params, which get copied from stat to geom by the layer)
        if self.params.get("jittered_points"):
            if "_jitter_data" not in self.params:
                self.params["_jitter_data"] = []
            self.params["_jitter_data"].append(
                _make_point_rows(data, y_value, dens, self.params)
            )

        return dens


def _assign_quantiles(
    dens: pd.DataFrame,
    raw_x: pd.Series,
    weight: np.ndarray | None,
    quantiles: int | list[float],
) -> pd.DataFrame:
    """Assign each density point to a quantile group.

    Parameters
    ----------
    dens : DataFrame
        Density output with ``x`` and ``density`` columns.
    raw_x : Series
        Original (pre-KDE) x observations for computing quantile
        boundaries via the empirical distribution.
    weight : array or None
        Observation weights.
    quantiles : int or list[float]
        If an integer *k*, split into *k* equal-probability groups.
        If a list of floats (each in (0, 1)), use those as cut points.
    """
    # Determine quantile cut points
    if isinstance(quantiles, int):
        probs = np.linspace(0, 1, quantiles + 1)[1:-1]
    else:
        probs = np.asarray(quantiles, dtype=float)
        probs = probs[(probs > 0) & (probs < 1)]

    if weight is not None and len(weight) == len(raw_x):
        # Weighted quantiles
        sorted_idx = np.argsort(raw_x)
        sorted_x = np.asarray(raw_x)[sorted_idx]
        sorted_w = np.asarray(weight)[sorted_idx]
        cum_w = np.cumsum(sorted_w)
        cum_w /= cum_w[-1]
        breaks = np.interp(probs, cum_w, sorted_x)
    else:
        breaks = np.quantile(raw_x, probs)

    # Assign each density-grid point to a quantile group (1-indexed)
    dens = dens.copy()
    dens["quantile"] = np.searchsorted(breaks, dens["x"].values, side="right") + 1
    return dens


def _make_point_rows(
    data: pd.DataFrame,
    y_value: object,
    dens: pd.DataFrame,
    params: dict,
) -> pd.DataFrame:
    """Create rows representing the original data points for jittering.

    Each point gets a ``datatype="point"`` marker so the geom can
    distinguish ridge rows from point rows.
    """
    seed = params.get("point_seed", 42)
    rng = np.random.default_rng(seed)

    points = pd.DataFrame(
        {
            "x": data["x"].values,
            "y": y_value,
            "density": np.interp(
                data["x"].values, dens["x"].values, dens["density"].values
            ),
            "ndensity": 0.0,  # filled in at panel level
            "scaled": 0.0,
            "count": 0.0,
            "n": 0.0,
            "datatype": "point",
            "height": 0.0,
        }
    )

    # Random y-offset within the density envelope (0 to density)
    points["point_jitter"] = rng.uniform(0, 1, len(points))

    # Carry over group and other aesthetic columns
    for col in data.columns:
        if col not in points.columns and col != "weight":
            points[col] = data[col].values

    return points
