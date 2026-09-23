"""Configured PlotEngine for CEMC recipes.

Wires the business pieces into the business-agnostic engine:

* ``FIELD_INFOS`` — recipe ``data.*.field`` names (aligned with cemc
  element names) mapped to ``FieldInfo`` objects;
* diagnostic compute ops registered on top of the engine built-ins
  (``wind_speed``; ``prep_classify`` for the rain/snow split);
* the process-wide default style registry (cedar-graph styles are
  injected via the ``cedarkit.plots.styles`` entry point).
"""

from types import MappingProxyType
from typing import Optional

from cedarkit.plots.engine import OpRegistry, PlotEngine
from cedarkit.plots.style import get_default_registry

from cedar_graph.data.field_info import field_info_from_parameter
from cedar_graph.recipes.plugins import _prep_classify, _wind_speed


# Frozen T2-01 migration matrix, retained only for old Python imports.
_LEGACY_FIELD_IDS = {
    "t2m": "cedarkit.t2m", "t": "cedarkit.t", "rh2m": "cedarkit.rh2m",
    "h": "cedarkit.h", "mslp": "cedarkit.psl", "u": "cedarkit.u",
    "v": "cedarkit.v", "cr": "cedarkit.cdbz", "apcp": "cedarkit.rain",
    "asnow": "cedarkit.sf", "div": "cedarkit.div", "kidx": "cedarkit.kidx",
    "cape": "cedarkit.cape", "cin": "cedarkit.cin", "bli": "cedarkit.bli",
    "qv_div": "cedarkit.qdiv", "dpt": "cedarkit.td", "pte": "cedarkit.theta-se",
    "vwsh": "cedarkit.shr",
}
_LEGACY_DISPLAY_NAMES = {"kidx": "k", "cin": "cape"}

# All T2-04 fields are represented by the parameter registry.
OVERRIDE_FIELDS = MappingProxyType({})
FIELD_INFOS = MappingProxyType({
    legacy_name: field_info_from_parameter(
        parameter_id, name=_LEGACY_DISPLAY_NAMES.get(legacy_name, legacy_name)
    )
    for legacy_name, parameter_id in _LEGACY_FIELD_IDS.items()
})
RECIPE_FIELDS = MappingProxyType(dict(FIELD_INFOS) | {
    parameter_id: field_info_from_parameter(
        parameter_id, name=_LEGACY_DISPLAY_NAMES.get(legacy_name, legacy_name)
    )
    for legacy_name, parameter_id in _LEGACY_FIELD_IDS.items()
} | dict(OVERRIDE_FIELDS))


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
            field_registry=RECIPE_FIELDS,
        )
    return _engine
