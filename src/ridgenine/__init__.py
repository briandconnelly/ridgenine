from importlib.metadata import version

from .geom_density_ridges import geom_density_ridges
from .geom_density_ridges_gradient import geom_density_ridges_gradient
from .geom_ridgeline import geom_ridgeline
from .stat_binline import stat_binline
from .stat_density_ridges import stat_density_ridges
from .theme_ridges import theme_ridges

__all__ = [
    "geom_density_ridges",
    "geom_density_ridges_gradient",
    "geom_ridgeline",
    "stat_binline",
    "stat_density_ridges",
    "theme_ridges",
]

__version__ = version("ridgenine")
