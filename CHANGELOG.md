# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `geom_density_ridges` — ridgeline plot with automatic kernel density estimation
- `geom_ridgeline` — lower-level geom for pre-computed heights
- `geom_density_ridges_gradient` — gradient-filled ridgeline plots with per-strip colouring
- `stat_density_ridges` — standalone stat for KDE computation
- `stat_binline` — histogram-style stepped ridgelines as an alternative to KDE
- `theme_ridges` — clean theme designed for ridgeline plots
- Support for `scale`, `rel_min_height`, `panel_scaling`, and `outline_type` parameters
- Quantile lines via `quantile_lines` and `quantiles` parameters on `geom_density_ridges`
- Quantile column (`after_stat("quantile")`) in `stat_density_ridges` output
- Jittered points via `jittered_points` parameter on `geom_density_ridges`
- Full composability with plotnine faceting, coord_flip, and aesthetic mappings
- `py.typed` marker for PEP 561 typed package support
- `ridgenine.__version__` attribute
- GitHub Actions CI for Python 3.10–3.13
- `[project.urls]` metadata for PyPI
