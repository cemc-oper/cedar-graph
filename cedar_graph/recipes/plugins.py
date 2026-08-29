"""Controlled cedar-graph providers for the PlotRecipe plugin groups.

Providers return data/descriptors only; importing this module does not mutate
cedarkit-plots global registries, so discovery order cannot affect results.
"""

from __future__ import annotations

from importlib.resources import files

import numpy as np
import xarray as xr

from cedarkit.plots.domains.registry import DomainDescriptor
from cedarkit.plots.ops.descriptor import OpDescriptor


def recipe_provider():
    """Expose packaged v2 recipe resources through Traversable semantics."""
    return files("cedar_graph.recipes")


def _wind_speed(u: xr.DataArray, v: xr.DataArray, *, context=None) -> xr.DataArray:
    return np.sqrt(u * u + v * v)


def _prep_classify(rain_total: xr.DataArray, snow_total: xr.DataArray, *, context=None):
    rain_total = xr.where(rain_total > 0, rain_total, np.nan)
    ratio = snow_total / rain_total
    return (
        xr.where(ratio < 0.25, rain_total, np.nan),
        xr.where(np.logical_and(ratio >= 0.25, ratio <= 0.75), rain_total, np.nan),
        xr.where(ratio > 0.75, rain_total, np.nan),
    )


def op_descriptors():
    return (
        OpDescriptor("wind_speed", "compute", 2, 1, _wind_speed, pure=True, reusable=True),
        OpDescriptor("prep_classify", "compute", 2, 3, _prep_classify, pure=True, reusable=True),
    )


def domain_descriptors():
    # Imports are intentionally deferred: plugin discovery itself remains
    # lightweight and does not pull plotting backends into the core package.
    from cedarkit.plots.domains import CnAreaMapTemplate, EastAsiaMapTemplate
    return (
        DomainDescriptor("east_asia", lambda metadata: EastAsiaMapTemplate()),
        DomainDescriptor("cn_area", lambda metadata: CnAreaMapTemplate(area=metadata.area_range)),
    )
