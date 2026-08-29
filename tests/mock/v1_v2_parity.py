"""Deterministic v1/v2 parity oracle for recipes migrated from Python plots.

The v1 plot modules were deliberately removed in commit ``23418f5``.  This
helper executes their immediately preceding revision from Git without adding
them back to the package, so a recipe is compared with the implementation it
replaced rather than with a compatibility facade.
"""

from __future__ import annotations

import subprocess
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np
import xarray as xr

from cedar_graph.data import DataLoader
from cedar_graph.recipes.engine import get_recipe_engine


# Parent of the commit which removed the 13 modules.  Keep this immutable
# historical oracle explicit: changing it requires review of all parity data.
HISTORICAL_REVISION = "23418f5^"


PRODUCTS: dict[str, dict[str, Any]] = {
    "bli_wind": {"recipe": "bli_wind", "params": {"wind_level": 850.0}, "pairs": (("field_bli", "bli"), ("field_u", "u"), ("field_v", "v"))},
    "cape_wind": {"recipe": "cape_wind", "params": {"wind_level": 850.0}, "pairs": (("field_cape", "cape"), ("field_u", "u"), ("field_v", "v"))},
    "cin_wind": {"recipe": "cin_wind", "params": {"wind_level": 850.0}, "pairs": (("field_cin", "cin"), ("field_u", "u"), ("field_v", "v"))},
    "height_500_mslp": {"recipe": "h_500_psl", "params": {}, "pairs": (("field_hgt_500", "h_500"), ("field_mslp", "psl"))},
    "height_500_wind_850": {"recipe": "h_500_wind_850", "params": {}, "pairs": (("field_hgt_500", "h_500"), ("field_u_850", "u_850"), ("field_v_850", "v_850"), ("field_wind_speed_850", "ws_850"))},
    "k_wind": {"recipe": "kidx_wind", "params": {"wind_level": 850.0}, "pairs": (("field_k", "kidx"), ("field_u", "u"), ("field_v", "v"))},
    "prep_24h": {"recipe": "prep_24h", "params": {}, "pairs": (("field_rain", "rain"), ("field_rain_snow", "rain_snow"), ("field_snow", "snow"))},
    "radar_reflectivity": {"recipe": "cdbz", "params": {}, "pairs": (("field_cr", "cdbz"),)},
    "rain_24h": {"recipe": "rain_24h", "params": {}, "pairs": (("field_rain", "rain"),)},
    "rain_wind_10m": {"recipe": "rain_wind_10m", "params": {"interval": pd.Timedelta(hours=24)}, "pairs": (("field_rain", "rain"), ("field_u", "u_10m"), ("field_v", "v_10m"))},
    "rh_2m": {"recipe": "rh2m", "params": {}, "pairs": (("field_rh_2m", "rh2m"),)},
    "t_2m": {"recipe": "t2m", "params": {}, "pairs": (("field_t_2m", "t2m"),)},
    "wind_10m": {"recipe": "wind_10m", "params": {}, "pairs": (("field_u_10m", "u_10m"), ("field_v_10m", "v_10m"), ("field_wind_speed_10m", "ws_10m"))},
}


def historical_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", HISTORICAL_REVISION], text=True
    ).strip()


def load_legacy_module(plot_name: str) -> types.ModuleType:
    path = f"cedar_graph/plots/cn/{plot_name}/default.py"
    source = subprocess.check_output(
        ["git", "show", f"{HISTORICAL_REVISION}:{path}"], text=True
    )
    module_name = f"cedar_graph._stage4_v1_oracle_{plot_name}"
    module = types.ModuleType(module_name)
    module.__file__ = f"git:{historical_sha()}:{path}"
    sys.modules[module_name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def load_v1_v2(plot_name: str, data_source: Any, start_time: pd.Timestamp, forecast_time: pd.Timedelta):
    spec = PRODUCTS[plot_name]
    params = spec["params"]
    legacy_module = load_legacy_module(plot_name)
    loader = DataLoader(data_source=data_source)
    legacy = legacy_module.load_data(loader, start_time, forecast_time, **params)
    recipe_path = Path(__file__).parents[2] / "cedar_graph" / "recipes" / "cn" / f"{spec['recipe']}.yaml"
    recipe_module = get_recipe_engine().build_module(get_recipe_engine().load_recipe(recipe_path))
    current = recipe_module.load_data(loader, start_time, forecast_time, **params)
    return legacy_module, legacy, recipe_module, current


def data_pairs(plot_name: str, legacy: Any, current: Any) -> Iterator[tuple[str, xr.DataArray, xr.DataArray]]:
    for legacy_name, current_name in PRODUCTS[plot_name]["pairs"]:
        old = getattr(legacy, legacy_name)
        new = getattr(current, current_name)
        assert isinstance(old, xr.DataArray)
        assert isinstance(new, xr.DataArray)
        yield f"{legacy_name}->{current_name}", old, new


def assert_data_parity(plot_name: str, legacy: Any, current: Any) -> list[dict[str, Any]]:
    evidence = []
    for binding, old, new in data_pairs(plot_name, legacy, current):
        # Structural metadata must match exactly.  Values use a frozen
        # machine-precision tolerance because v1's Python arithmetic and the
        # v2 operation graph can differ only in floating-point grouping.
        assert old.name == new.name
        assert old.dims == new.dims
        assert old.shape == new.shape
        assert old.dtype == new.dtype
        assert old.attrs == new.attrs
        assert old.coords.identical(new.coords)
        xr.testing.assert_allclose(old, new, rtol=1e-12, atol=1e-12)
        difference = np.asarray(old.values) - np.asarray(new.values)
        evidence.append({
            "binding": binding,
            "name": old.name,
            "dims": list(old.dims),
            "shape": list(old.shape),
            "dtype": str(old.dtype),
            "units": old.attrs.get("units"),
            "nan_count": int(old.isnull().sum().item()),
            "min": float(old.min(skipna=True).item()),
            "max": float(old.max(skipna=True).item()),
            "mean": float(old.mean(skipna=True).item()),
            "max_abs_difference": float(np.nanmax(np.abs(difference))),
        })
    return evidence
