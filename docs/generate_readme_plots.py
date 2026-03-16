"""Generate the plots embedded in README.md."""

import pandas as pd
from plotnine import (
    aes,
    facet_wrap,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)
from plotnine.data import diamonds, penguins

from ridgenine import geom_density_ridges, theme_ridges

# ── Plot 1: penguins — the "hello world" ─────────────────────────────────────

p1 = (
    ggplot(penguins.dropna(), aes("flipper_length_mm", "species", fill="species"))
    + geom_density_ridges(scale=1.8, alpha=0.8)
    + scale_fill_manual(values=["#4E79A7", "#F28E2B", "#59A14F"])
    + labs(x="Flipper length (mm)", y=None)
    + theme_ridges()
    + theme(legend_position="none", figure_size=(6, 3.5))
)
p1.save("docs/example_penguins.png", dpi=150, verbose=False)
print("saved docs/example_penguins.png")


# ── Plot 2: diamonds — carat by cut quality ──────────────────────────────────
# Better-cut diamonds tend to be smaller: jewelers sacrifice carat weight
# for optical quality. Sequential fill reinforces the quality ordering.

cut_order = ["Fair", "Good", "Very Good", "Premium", "Ideal"]
diamonds_ordered = diamonds.copy()
diamonds_ordered["cut"] = pd.Categorical(
    diamonds_ordered["cut"], categories=cut_order, ordered=True
)

p2 = (
    ggplot(diamonds_ordered, aes("carat", "cut", fill="cut"))
    + geom_density_ridges(scale=2.0, alpha=0.9, trim=True)
    + scale_fill_manual(
        values=["#d0e8f5", "#85c1e2", "#3d9fcc", "#1a6fa3", "#0d4f7a"]
    )
    + scale_x_continuous(limits=(0, 3))
    + labs(
        title="Better cut diamonds tend to be smaller",
        subtitle="Jewelers sacrifice carat weight for optical quality",
        x="Carat",
        y=None,
    )
    + theme_minimal()
    + theme(legend_position="none", figure_size=(6, 4.5))
)
p2.save("docs/example_diamonds.png", dpi=150, verbose=False)
print("saved docs/example_diamonds.png")


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
