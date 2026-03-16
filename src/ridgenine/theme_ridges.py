from __future__ import annotations

from plotnine.themes.elements import element_blank, element_line, element_text
from plotnine.themes.theme import theme
from plotnine.themes.theme_minimal import theme_minimal


def theme_ridges(
    font_size: int = 14, line_size: float = 0.5, grid: bool = True
) -> theme:
    """
    A clean theme designed for ridgeline plots.

    Analogous to ``ggridges::theme_ridges``. Removes horizontal grid lines
    (which are obscured by the ridges anyway), keeps subtle vertical guides,
    and uses a slightly larger base font size than plotnine's default.

    Parameters
    ----------
    font_size : int, default=14
        Base font size in points.
    line_size : float, default=0.5
        Thickness of axis lines and tick marks.
    grid : bool, default=True
        If ``True``, draw vertical grid lines. Set to ``False`` for a
        completely clean background.

    Returns
    -------
    theme
        A plotnine ``theme`` object that can be added to any plot with ``+``.

    Examples
    --------
    .. code-block:: python

        from plotnine import ggplot, aes
        from ridgenine import geom_density_ridges, theme_ridges

        (
            ggplot(df, aes("x", "category"))
            + geom_density_ridges()
            + theme_ridges()
        )
    """
    base = theme_minimal(base_size=font_size)
    adjustments = theme(
        # Remove horizontal grid lines — ridges sit on top of them anyway
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
        # Keep minor x grid off; major x grid controlled by `grid` param
        panel_grid_minor_x=element_blank(),
        # Subtle left axis line and ticks
        axis_line_x=element_line(size=line_size),
        # Align y-axis labels to the baseline of each ridge
        axis_text_y=element_text(vjust=0),
    )
    if not grid:
        adjustments += theme(panel_grid_major_x=element_blank())

    return base + adjustments
