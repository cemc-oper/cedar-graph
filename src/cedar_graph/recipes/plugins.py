"""Controlled cedar-graph providers for the PlotRecipe plugin groups.

Providers return data/descriptors only; importing this module does not mutate
cedarkit-plots global registries, so discovery order cannot affect results.
"""

from __future__ import annotations

from importlib.resources import files

import numpy as np
import xarray as xr

from cedarkit.plots.ops.descriptor import OpDescriptor
from cedarkit.plots.units import canonical_unit


def recipe_provider():
    """Expose packaged v2 recipe resources through Traversable semantics."""
    return files("cedar_graph.recipes")


def _wind_speed(u: xr.DataArray, v: xr.DataArray, *, context=None) -> xr.DataArray:
    u_unit, v_unit = u.attrs.get("units"), v.attrs.get("units")
    if u_unit is not None and v_unit is not None and canonical_unit(u_unit) != canonical_unit(v_unit):
        raise ValueError(f"wind components have different units: {u_unit!r}, {v_unit!r}")
    result = np.sqrt(u * u + v * v)
    result.attrs = dict(u.attrs)
    if u_unit is None and v_unit is not None:
        result.attrs["units"] = v_unit
    return result


def _prep_classify(rain_total: xr.DataArray, snow_total: xr.DataArray, *, context=None):
    rain_total = xr.where(rain_total > 0, rain_total, np.nan)
    ratio = snow_total / rain_total
    result = (
        xr.where(ratio < 0.25, rain_total, np.nan),
        xr.where(np.logical_and(ratio >= 0.25, ratio <= 0.75), rain_total, np.nan),
        xr.where(ratio > 0.75, rain_total, np.nan),
    )
    for field in result:
        field.attrs = dict(rain_total.attrs)
    return result


def _temperature_difference(first: xr.DataArray, second: xr.DataArray, *, context=None) -> xr.DataArray:
    """Subtract two absolute Kelvin fields and label the result as a difference."""
    if canonical_unit(first.attrs.get("units", "")) != "K" or canonical_unit(second.attrs.get("units", "")) != "K":
        raise ValueError("temperature_difference requires two Kelvin fields")
    if first.attrs.get("temperature_kind") != "absolute" or second.attrs.get("temperature_kind") != "absolute":
        raise ValueError("temperature_difference requires absolute temperatures")
    result = first - second
    result.attrs = {"units": "K", "temperature_kind": "difference"}
    return result


def op_descriptors():
    return (
        OpDescriptor("wind_speed", "compute", 2, 1, _wind_speed, pure=True, reusable=True),
        OpDescriptor("prep_classify", "compute", 2, 3, _prep_classify, pure=True, reusable=True),
        OpDescriptor("temperature_difference", "compute", 2, 1, _temperature_difference,
                     pure=True, reusable=True),
    )
