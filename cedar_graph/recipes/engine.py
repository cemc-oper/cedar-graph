"""Configured PlotEngine for CEMC recipes.

Wires the business pieces into the business-agnostic engine:

* ``FIELD_INFOS`` — recipe ``data.*.field`` names (aligned with cemc
  element names) mapped to ``FieldInfo`` objects;
* diagnostic compute ops registered on top of the engine built-ins
  (``wind_speed``; ``prep_classify`` for the rain/snow split);
* the process-wide default style registry (cedar-graph styles are
  injected via the ``cedarkit.plots.styles`` entry point).
"""

from typing import Optional

import numpy as np
import xarray as xr

from cedarkit.plots.engine import OpRegistry, PlotEngine
from cedarkit.plots.style import get_default_registry

from cedar_graph.data.field_info import (
    apcp_info,
    asnow_info,
    bli_info,
    cape_info,
    cin_info,
    cr_info,
    dew_t_info,
    div_info,
    hgt_info,
    k_index_info,
    mslp_info,
    pte_info,
    qv_div_info,
    rh_2m_info,
    t_2m_info,
    t_info,
    u_info,
    v_info,
    vwsh_info,
)

#: recipe field name -> FieldInfo. Keys are cemc element names where one
#: exists; ``mslp``/``cr`` keep the names used by the current plot modules.
FIELD_INFOS = {
    "t2m": t_2m_info,
    "t": t_info,
    "rh2m": rh_2m_info,
    "h": hgt_info,
    "mslp": mslp_info,
    "u": u_info,
    "v": v_info,
    "cr": cr_info,
    "apcp": apcp_info,
    "asnow": asnow_info,
    "div": div_info,
    "kidx": k_index_info,
    "cape": cape_info,
    "cin": cin_info,
    "bli": bli_info,
    "qv_div": qv_div_info,
    "dpt": dew_t_info,
    "pte": pte_info,
    "vwsh": vwsh_info,
}


def _wind_speed(u: xr.DataArray, v: xr.DataArray, context) -> xr.DataArray:
    """Wind speed from u/v components (sqrt(u^2 + v^2))."""
    return np.sqrt(u * u + v * v)


def _prep_classify(rain_total: xr.DataArray, snow_total: xr.DataArray, context):
    """
    Split total precipitation into rain / rain-snow mix / snow by the
    snow-to-rain ratio (< 0.25 rain, > 0.75 snow, in between mix);
    non-positive totals are masked out.
    """
    rain_total = xr.where(rain_total > 0, rain_total, np.nan)
    ratio = snow_total / rain_total
    field_rain = xr.where(ratio < 0.25, rain_total, np.nan)
    field_rain_snow = xr.where(np.logical_and(ratio >= 0.25, ratio <= 0.75), rain_total, np.nan)
    field_snow = xr.where(ratio > 0.75, rain_total, np.nan)
    return field_rain, field_rain_snow, field_snow


def create_op_registry() -> OpRegistry:
    """Engine built-ins plus CEMC diagnostic ops."""
    registry = OpRegistry.builtins()
    registry.register("wind_speed", _wind_speed, kind="compute")
    registry.register("prep_classify", _prep_classify, kind="compute")
    return registry


_engine: Optional[PlotEngine] = None


def get_recipe_engine() -> PlotEngine:
    """Process-wide recipe engine, created lazily."""
    global _engine
    if _engine is None:
        _engine = PlotEngine(
            style_registry=get_default_registry(),
            op_registry=create_op_registry(),
            field_registry=FIELD_INFOS,
        )
    return _engine
