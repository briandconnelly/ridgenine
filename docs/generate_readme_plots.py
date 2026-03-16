"""Generate the plots embedded in README.md."""

import pandas as pd
from plotnine import (
    aes,
    facet_wrap,
    ggplot,
    labs,
    scale_fill_brewer,
    scale_fill_manual,
    theme,
    theme_classic,
    theme_minimal,
)
from plotnine.data import mpg, penguins

from ridgenine import geom_density_ridges

# ── Plot 1: penguins — the "hello world" ─────────────────────────────────────

p1 = (
    ggplot(penguins.dropna(), aes("flipper_length_mm", "species", fill="species"))
    + geom_density_ridges(scale=1.8, alpha=0.8)
    + scale_fill_manual(values=["#4E79A7", "#F28E2B", "#59A14F"])
    + labs(x="Flipper length (mm)", y=None)
    + theme_classic()
    + theme(legend_position="none", figure_size=(6, 3.5))
)
p1.save("docs/example_penguins.png", dpi=150, verbose=False)
print("saved docs/example_penguins.png")


# ── Plot 2: mpg ordered by median — shows scale overlap ──────────────────────

class_order = mpg.groupby("class")["hwy"].median().sort_values().index.tolist()
mpg_ordered = mpg.copy()
mpg_ordered["class"] = pd.Categorical(
    mpg_ordered["class"], categories=class_order, ordered=True
)

p2 = (
    ggplot(mpg_ordered, aes("hwy", "class", fill="class"))
    + geom_density_ridges(scale=2.5, alpha=0.75, trim=True)
    + scale_fill_brewer(type="qual", palette="Set2")
    + labs(x="Highway MPG", y=None)
    + theme_minimal()
    + theme(legend_position="none", figure_size=(6, 4))
)
p2.save("docs/example_mpg.png", dpi=150, verbose=False)
print("saved docs/example_mpg.png")


# ── Plot 3: facets ────────────────────────────────────────────────────────────

p3 = (
    ggplot(penguins.dropna(), aes("bill_length_mm", "species", fill="species"))
    + geom_density_ridges(scale=1.5, alpha=0.75)
    + scale_fill_manual(values=["#4E79A7", "#F28E2B", "#59A14F"])
    + facet_wrap("island")
    + labs(x="Bill length (mm)", y=None)
    + theme_minimal()
    + theme(legend_position="none", figure_size=(8, 3.5))
)
p3.save("docs/example_faceted.png", dpi=150, verbose=False)
print("saved docs/example_faceted.png")
