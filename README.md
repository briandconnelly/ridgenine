# ridgenine

Ridgeline plots for [plotnine](https://plotnine.org/), inspired by the
[ggridges](https://wilkelab.org/ggridges/) package for ggplot2.

Ridgeline plots display the distribution of a continuous variable across
multiple categories as a series of overlapping density curves — useful for
comparing many distributions at once in a compact, readable layout.

![Penguin flipper length by species](docs/example_penguins.png)

---

## Installation

**pip**

```bash
pip install ridgenine
```

**uv**

```bash
uv add ridgenine
```

---

## Quick start

```python
from plotnine import ggplot, aes
from ridgenine import geom_density_ridges, theme_ridges

(
    ggplot(df, aes("value", "category"))
    + geom_density_ridges()
    + theme_ridges()
)
```

---

## Examples

### Density ridges

`geom_density_ridges` estimates a kernel density for each category and draws
it as a filled ridge. The `scale` parameter controls overlap: `scale=1` means
the tallest ridge exactly reaches the next category's baseline; values above 1
cause overlap, values below 1 leave gaps. Pair with `theme_ridges()` for a
clean, purpose-built look.

Here, a sequential fill palette reinforces the ordering — darker blue means
higher cut quality — revealing that better-cut diamonds tend to be smaller.

```python
import pandas as pd
from plotnine import ggplot, aes, scale_fill_manual, scale_x_continuous
from plotnine.data import diamonds
from ridgenine import geom_density_ridges

cut_order = ["Fair", "Good", "Very Good", "Premium", "Ideal"]
diamonds["cut"] = pd.Categorical(diamonds["cut"], categories=cut_order, ordered=True)

(
    ggplot(diamonds, aes("carat", "cut", fill="cut"))
    + geom_density_ridges(scale=2.0, alpha=0.9, trim=True)
    + scale_fill_manual(values=["#d0e8f5", "#85c1e2", "#3d9fcc", "#1a6fa3", "#0d4f7a"])
    + scale_x_continuous(limits=(0, 3))
)
```

![Diamond carat by cut quality](docs/example_diamonds.png)

### Faceting

`geom_density_ridges` composes naturally with the rest of plotnine's grammar,
including `facet_wrap` and `facet_grid`.

```python
from plotnine import ggplot, aes, facet_wrap, scale_fill_manual
from plotnine.data import penguins
from ridgenine import geom_density_ridges

(
    ggplot(penguins.dropna(), aes("bill_length_mm", "species", fill="species"))
    + geom_density_ridges(scale=1.5, alpha=0.75)
    + scale_fill_manual(values=["#4E79A7", "#F28E2B", "#59A14F"])
    + facet_wrap("island")
)
```

![Penguin bill length by species, faceted by island](docs/example_faceted.png)


---

## API

### `geom_density_ridges`

The primary geom. Computes a KDE for each `y` category and draws it as a
filled ridge.

| Parameter | Default | Description |
|---|---|---|
| `scale` | `1.0` | Ridge height multiplier. Values > 1 cause overlap. |
| `rel_min_height` | `0` | Clip density tails below this fraction of the panel-wide peak to the baseline. E.g. `0.01` removes the bottom 1% of each ridge's tails. |
| `panel_scaling` | `True` | If `True`, normalise heights per panel. If `False`, normalise globally so ridge heights are comparable across facets. |
| `kernel` | `"gaussian"` | KDE kernel (same options as `stat_density`). |
| `bw` | `"nrd0"` | Bandwidth or bandwidth method. |
| `adjust` | `1` | Bandwidth multiplier. |
| `trim` | `False` | Trim density to the data range of each group. |
| `n` | `512` | Number of density evaluation points per group. |
| `outline_type` | `"upper"` | Which boundary to stroke: `"upper"`, `"lower"`, `"both"`, `"full"`. |

The `height` aesthetic defaults to `after_stat("ndensity")` (density
normalised to [0, 1] across the whole panel). Override it to use raw density
or counts:

```python
from plotnine.mapping.evaluation import after_stat

# Area proportional to number of observations
ggplot(df, aes("x", "y", height=after_stat("count"))) + geom_density_ridges()
```

### `geom_ridgeline`

Lower-level geom for pre-computed heights. Requires `x`, `y`, and `height`
aesthetics. The `height` value at each `x` point controls how far above the
category baseline the ridge extends. Accepts the same `scale` and
`outline_type` parameters as `geom_density_ridges`.

### `stat_density_ridges`

The stat underlying `geom_density_ridges`. Can be used independently to
attach density computation to another geom.

### `theme_ridges`

A clean theme designed for ridgeline plots, analogous to `ggridges::theme_ridges`.
Removes horizontal grid lines (obscured by the ridges), keeps subtle vertical
guides, and uses a slightly larger base font size.

| Parameter | Default | Description |
|---|---|---|
| `font_size` | `14` | Base font size in points. |
| `line_size` | `0.5` | Thickness of axis lines and tick marks. |
| `grid` | `True` | If `False`, remove vertical grid lines for a completely clean background. |

---

## Credits

ridgenine is a port of [ggridges](https://wilkelab.org/ggridges/) by
[Claus O. Wilke](https://clauswilke.com/) to the Python / plotnine ecosystem.

---

## License

[MIT](LICENSE)
