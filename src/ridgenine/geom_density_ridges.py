from __future__ import annotations

import numpy as np

from plotnine.mapping.evaluation import after_stat

from .geom_ridgeline import geom_ridgeline


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
    }
