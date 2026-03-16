"""Generate the plots embedded in README.md."""

import pandas as pd
from plotnine import (
    aes,
    facet_wrap,
    ggplot,
    labs,
    scale_fill_gradient,
    scale_fill_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)
from plotnine.data import diamonds, penguins
from plotnine.mapping.evaluation import after_stat

from ridgenine import (
    geom_density_ridges,
    geom_density_ridges_gradient,
    geom_ridgeline,
    theme_ridges,
)

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


# ── Plot 3: gradient fills ───────────────────────────────────────────────────

p3g = (
    ggplot(
        penguins.dropna(),
        aes("flipper_length_mm", "species", fill=after_stat("x")),
    )
    + geom_density_ridges_gradient(scale=1.5, alpha=0.9)
    + scale_fill_gradient(low="#2c7bb6", high="#d7191c")
    + labs(x="Flipper length (mm)", y=None)
    + theme_ridges()
    + theme(legend_position="none", figure_size=(6, 3.5))
)
p3g.save("docs/example_gradient.png", dpi=150, verbose=False)
print("saved docs/example_gradient.png")


# ── Plot 4: quantile lines ──────────────────────────────────────────────────

p4 = (
    ggplot(penguins.dropna(), aes("flipper_length_mm", "species", fill="species"))
    + geom_density_ridges(scale=1.5, alpha=0.7, quantile_lines=True)
    + scale_fill_manual(values=["#4E79A7", "#F28E2B", "#59A14F"])
    + labs(x="Flipper length (mm)", y=None)
    + theme_ridges()
    + theme(legend_position="none", figure_size=(6, 3.5))
)
p4.save("docs/example_quantile_lines.png", dpi=150, verbose=False)
print("saved docs/example_quantile_lines.png")


# ── Plot 5: jittered points ─────────────────────────────────────────────────

p5 = (
    ggplot(penguins.dropna(), aes("flipper_length_mm", "species", fill="species"))
    + geom_density_ridges(
        scale=1.5, alpha=0.6,
        jittered_points=True, point_size=0.5, point_alpha=0.4,
    )
    + scale_fill_manual(values=["#4E79A7", "#F28E2B", "#59A14F"])
    + labs(x="Flipper length (mm)", y=None)
    + theme_ridges()
    + theme(legend_position="none", figure_size=(6, 3.5))
)
p5.save("docs/example_jittered_points.png", dpi=150, verbose=False)
print("saved docs/example_jittered_points.png")


# ── Plot 6: histogram ridges (stat_binline) ──────────────────────────────────

p6 = (
    ggplot(penguins.dropna(), aes("flipper_length_mm", "species", fill="species"))
    + geom_ridgeline(stat="binline", bins=20, scale=1.5, alpha=0.7)
    + scale_fill_manual(values=["#4E79A7", "#F28E2B", "#59A14F"])
    + labs(x="Flipper length (mm)", y=None)
    + theme_ridges()
    + theme(legend_position="none", figure_size=(6, 3.5))
)
p6.save("docs/example_binline.png", dpi=150, verbose=False)
print("saved docs/example_binline.png")


# ── Plot 7: facets ───────────────────────────────────────────────────────────

p7 = (
    ggplot(penguins.dropna(), aes("bill_length_mm", "species", fill="species"))
    + geom_density_ridges(scale=1.5, alpha=0.75)
    + scale_fill_manual(values=["#4E79A7", "#F28E2B", "#59A14F"])
    + facet_wrap("island")
    + labs(x="Bill length (mm)", y=None)
    + theme_minimal()
    + theme(legend_position="none", figure_size=(8, 3.5))
)
p7.save("docs/example_faceted.png", dpi=150, verbose=False)
print("saved docs/example_faceted.png")


# ── Plot 8: outline types comparison ─────────────────────────────────────────
# Side-by-side comparison of all four outline_type values

import numpy as np
from plotnine import facet_grid, ggtitle

rng = np.random.default_rng(42)
outline_df = pd.concat([
    pd.DataFrame({
        "x": rng.normal(0, 1, 200),
        "y": "A",
        "outline": otype,
    })
    for otype in ["upper", "lower", "both", "full"]
], ignore_index=True)
outline_df["outline"] = pd.Categorical(
    outline_df["outline"],
    categories=["upper", "lower", "both", "full"],
    ordered=True,
)

plots = []
for otype in ["upper", "lower", "both", "full"]:
    sub = outline_df[outline_df["outline"] == otype]
    p = (
        ggplot(sub, aes("x", "y"))
        + geom_density_ridges(scale=0.9, alpha=0.7, fill="#4E79A7", outline_type=otype)
        + ggtitle(f'outline_type="{otype}"')
        + labs(x=None, y=None)
        + theme_minimal()
        + theme(figure_size=(2.5, 1.5), plot_title=theme_minimal().themeables.get("plot_title"))
    )
    plots.append(p)

# Use patchwork-style composition if available, otherwise save individually
# and compose with a simple grid
from plotnine import save_as_pdf_pages
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

fig, axes = plt.subplots(1, 4, figsize=(10, 2.5))
for i, otype in enumerate(["upper", "lower", "both", "full"]):
    sub = outline_df[outline_df["outline"] == otype].copy()
    sub["y"] = 0.0  # numeric y for single category
    from ridgenine.geom_ridgeline import geom_ridgeline
    from plotnine._utils import resolution
    ax = axes[i]
    # Simple manual rendering
    from scipy.stats import gaussian_kde
    x_vals = sub["x"].values
    kde = gaussian_kde(x_vals)
    xs = np.linspace(x_vals.min() - 1, x_vals.max() + 1, 200)
    ys = kde(xs)
    ys = ys / ys.max() * 0.8  # normalise

    ax.fill_between(xs, 0, ys, alpha=0.7, color="#4E79A7")

    if otype in ("upper", "both"):
        ax.plot(xs, ys, color="#333333", linewidth=1)
    if otype in ("lower", "both"):
        ax.plot(xs, np.zeros_like(xs), color="#333333", linewidth=1)
    if otype == "full":
        ax.plot(
            np.concatenate([xs, xs[::-1]]),
            np.concatenate([ys, np.zeros_like(ys)]),
            color="#333333", linewidth=1,
        )

    ax.set_title(f'"{otype}"', fontsize=11)
    ax.set_xlim(xs.min(), xs.max())
    ax.set_ylim(-0.05, 1.0)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

fig.suptitle("outline_type", fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig("docs/example_outline_types.png", dpi=150, bbox_inches="tight")
print("saved docs/example_outline_types.png")
