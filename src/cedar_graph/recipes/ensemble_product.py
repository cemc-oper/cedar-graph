"""Caller-owned EnsCN charts backed by per-member v3 data plans."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from types import MappingProxyType
from typing import Any, Literal, Mapping

import cartopy.crs as ccrs
import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.plots import Panel
from cedarkit.plots.config import BasemapSpec, Cell, Rect, LayoutSpec
from cedarkit.plots.style.registry import get_default_registry
from cedarkit.plots.templates import ens_cn
from cedarkit.plots.workflow.discovery import discover_workflow
from cedarkit.plots.workflow.plan import CompileContext, compile_recipe
from cedarkit.plots.workflow.runtime import PlanExecutionError


class MissingMemberError(ValueError):
    """A requested member has no field in the configured source."""


def _member_id(value: Any) -> str:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise ValueError("member IDs must be non-empty strings without whitespace")
    if value == "max":
        raise ValueError("member ID 'max' is reserved for the statistical chart")
    return value


def _native_member(value: str):
    if value.lower() in {"ctl", "control"}:
        return 0
    return int(value.removeprefix("m")) if re.fullmatch(r"m?\d+", value) else value


@dataclass(frozen=True)
class EnsembleRequest:
    member_ids: tuple[str, ...]
    control_id: str | None = None
    include_control_in_max: bool = False
    missing_policy: Literal["error", "skip"] = "error"
    max_enabled: bool = True
    columns: int = 5
    style_variant: Literal["cn_summer", "cn_winter"] | None = None
    model: str = "Ensemble"

    def __post_init__(self) -> None:
        if not isinstance(self.member_ids, (list, tuple)):
            raise ValueError("member_ids must be a list or tuple")
        ids = tuple(_member_id(value) for value in self.member_ids)
        if not ids or len({_native_member(value) for value in ids}) != len(ids):
            raise ValueError("member_ids must be non-empty and unique")
        object.__setattr__(self, "member_ids", ids)
        if self.control_id is not None:
            control = _member_id(self.control_id)
            if _native_member(control) in {_native_member(value) for value in ids}:
                raise ValueError("control_id must be distinct from member_ids")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("model must be a non-empty string")
        if any(value.lower() in {"ctl", "control"} for value in ids):
            raise ValueError("put control aliases in control_id, not member_ids")
        if self.include_control_in_max and self.control_id is None:
            raise ValueError("include_control_in_max requires control_id")
        if not isinstance(self.include_control_in_max, bool) or not isinstance(self.max_enabled, bool):
            raise ValueError("MAX flags must be booleans")
        if self.missing_policy not in ("error", "skip"):
            raise ValueError("missing_policy must be 'error' or 'skip'")
        if isinstance(self.columns, bool) or not isinstance(self.columns, int) or self.columns < 1:
            raise ValueError("columns must be a positive integer")
        if self.style_variant not in (None, "cn_summer", "cn_winter"):
            raise ValueError("unknown temperature style variant")

    @classmethod
    def from_params(cls, params: Mapping[str, Any]) -> "EnsembleRequest":
        unknown = set(params) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"unknown ensemble parameters: {sorted(unknown)}")
        if "member_ids" not in params:
            raise ValueError("member_ids is required")
        return cls(**dict(params))


class _MissingAwareProvider:
    def __init__(self, provider: Any, member_id: str):
        self.provider, self.member_id = provider, member_id

    def fetch_many(self, requests):
        values = tuple(self.provider.fetch_many(requests) if hasattr(self.provider, "fetch_many")
                       else (self.provider.fetch(request) for request in requests))
        if any(value is None for value in values):
            raise MissingMemberError(f"member {self.member_id!r} has no temperature field")
        return values


@dataclass(frozen=True)
class PreparedEnsemble:
    request: EnsembleRequest
    fields: Mapping[str, xr.DataArray]
    realized_member_ids: tuple[str, ...]
    missing_member_ids: tuple[str, ...]
    realized_control_id: str | None
    max_input_ids: tuple[str, ...]
    max_field: xr.DataArray | None
    style_variant: str
    provider_requests: int
    max_valid_count: xr.DataArray | None
    start_time: str
    valid_time: str
    forecast_hours: float

    def summary(self) -> dict[str, Any]:
        """Describe the selected population and realized MAX inputs, never a probability."""
        requested = len(self.request.member_ids) + int(self.request.include_control_in_max)
        return {
            "requested_member_ids": list(self.request.member_ids),
            "realized_member_ids": list(self.realized_member_ids),
            "missing_member_ids": list(self.missing_member_ids),
            "requested_control_id": self.request.control_id,
            "realized_control_id": self.realized_control_id,
            "include_control_in_max": self.request.include_control_in_max,
            "max_enabled": self.request.max_enabled,
            "max_input_ids": list(self.max_input_ids),
            "max_requested_input_count": requested if self.request.max_enabled else 0,
            "max_realized_input_count": len(self.max_input_ids),
            "valid_input_count_min": None if self.max_valid_count is None else int(self.max_valid_count.min()),
            "valid_input_count_max": None if self.max_valid_count is None else int(self.max_valid_count.max()),
            "missing_policy": self.request.missing_policy,
            "statistic": "pointwise maximum of selected realized inputs; NaNs excluded, all-missing stays NaN",
            "population_scope": "explicitly selected subset; not a claim about the complete model ensemble",
            "model": self.request.model, "units": "degC",
            "start_time": self.start_time, "valid_time": self.valid_time,
        }

    def render(self, *, columns: int | None = None, basemap: BasemapSpec | None = None,
               empty_slots: Mapping[str, Cell | Rect] | None = None, render: bool = True) -> Panel:
        """Build Charts from prepared fields; reflow never reruns data plans."""
        column_count = self.request.columns if columns is None else columns
        panel = Panel(template=ens_cn(columns=column_count, control_id=self.realized_control_id,
                                      max_id="max" if self.max_field is not None else None,
                                      require_control=self.realized_control_id is not None,
                                      require_max=self.max_field is not None,
                                      basemap=basemap, empty_slots=empty_slots))
        try:
            origin, valid = pd.Timestamp(self.start_time), pd.Timestamp(self.valid_time)
            panel.set_title(f"{self.request.model} 2 m temperature (°C) | Init {origin:%Y%m%d%H} UTC | "
                            f"Valid {valid:%Y%m%d%H} UTC | +{self.forecast_hours:03g}h")
            styles = get_default_registry()
            layers = []
            ordered = ([self.realized_control_id] if self.realized_control_id else []) + list(self.realized_member_ids)
            if self.max_field is not None:
                ordered.append("max")
            for chart_id in ordered:
                role = "control" if chart_id == self.realized_control_id else ("max" if chart_id == "max" else "member")
                field = self.max_field if chart_id == "max" else self.fields[chart_id]
                chart = panel.add_chart(id=chart_id, role=role)
                title = "CTL" if role == "control" else chart_id
                if role == "max":
                    summary = self.summary()
                    title = (f"MAX n={len(self.max_input_ids)}/{summary['max_requested_input_count']}\n"
                             f"CTL {'included' if self.request.include_control_in_max else 'excluded'} · "
                             f"valid/cell {summary['valid_input_count_min']}–{summary['valid_input_count_max']}")
                chart.set_title(title)
                style = styles.get_style(f"cemc.t2m:{self.style_variant}", data=field)
                layers.append(chart.contourf(field, style=style, id="temperature",
                                             data_crs=ccrs.PlateCarree(), subplots="main"))
            panel.colorbar(tuple(layers), id="ens_cn_colorbar", label="°C", subplots="main")
            rows = panel.effective_config.layout.rows
            panel.configure(layout=LayoutSpec(figsize=(column_count * 3.6 + .8, rows * 2.5 + .8)))
            if render:
                panel.render()
            return panel
        except BaseException:
            panel.close()
            raise


@dataclass(frozen=True)
class EnsembleT2MProduct:
    name: str = "cn.ens_t2m"

    def compile_members(self, *, start_time: Any, forecast_time: Any,
                        request: EnsembleRequest):
        """Compile the same member reads used by prepare, without opening data."""
        discovered = discover_workflow()
        recipe = discovered.recipes.load("cn.ens_t2m_member")
        variant = request.style_variant or ("cn_summer" if 5 <= pd.Timestamp(start_time).month <= 9 else "cn_winter")
        ids = ((request.control_id,) if request.control_id else ()) + request.member_ids
        return {member_id: compile_recipe(recipe, CompileContext(
            start_time=start_time, forecast_time=forecast_time,
            params={"member_id": member_id, "member_role": "control" if member_id == request.control_id else "perturbation", "style_variant": variant}, cardinality="all"),
            registry=discovered.ops) for member_id in ids}

    def prepare(self, provider: Any, *, start_time: Any, forecast_time: Any,
                request: EnsembleRequest) -> PreparedEnsemble:
        discovered = discover_workflow()
        plans = self.compile_members(start_time=start_time, forecast_time=forecast_time, request=request)
        variant = request.style_variant or ("cn_summer" if 5 <= pd.Timestamp(start_time).month <= 9 else "cn_winter")
        fields: dict[str, xr.DataArray] = {}
        missing: list[str] = []
        realized: list[str] = []
        reads = 0
        candidates = ([request.control_id] if request.control_id else []) + list(request.member_ids)
        for member_id in candidates:
            plan = plans[member_id]
            try:
                result = plan.execute(_MissingAwareProvider(provider, member_id), registry=discovered.ops)
            except PlanExecutionError as exc:
                if isinstance(exc.cause, MissingMemberError) and request.missing_policy == "skip":
                    missing.append(member_id)
                    reads += plan.read_count
                    continue
                raise
            field = result.outputs["temperature"].copy(deep=False)
            field.attrs = {**field.attrs, "standard_name": "air_temperature"}
            if np.isinf(field.values).any():
                raise ValueError(f"ensemble member {member_id!r} has infinite temperature values")
            if "field_identity" in field.attrs:
                identity = json.loads(field.attrs["field_identity"])
                origin = pd.Timestamp(start_time)
                origin = origin.tz_localize("UTC") if origin.tzinfo is None else origin.tz_convert("UTC")
                role = "control" if member_id == request.control_id else "perturbation"
                if (identity.get("parameter") != "cedarkit.t2m" or identity.get("member") != _native_member(member_id)
                        or identity.get("member_role") != role or pd.Timestamp(identity["time"]) != origin
                        or pd.Timestamp(identity["valid_time"]) != origin + pd.Timedelta(forecast_time)
                        or identity.get("level_type") != "height_above_ground" or identity.get("level") != 2):
                    raise ValueError(f"ensemble member {member_id!r} has inconsistent identity or clocks")
            fields[member_id] = field
            reads += plan.read_count
            if member_id != request.control_id:
                realized.append(member_id)
        if not realized:
            raise ValueError("ensemble has no available members")
        control = request.control_id if request.control_id in fields else None
        if request.include_control_in_max and control is None:
            raise ValueError("requested MAX input control is missing")
        max_inputs = tuple(realized) + ((control,) if request.include_control_in_max else ())
        maximum = None
        valid_count = None
        if request.max_enabled:
            # GRIB carries the member number as a scalar coordinate.  It is
            # identity metadata, not part of the spatial grid for MAX.
            inputs = [field.reset_coords(
                [name for name in ("number", "member", "member_role")
                 if name in field.coords and field.coords[name].ndim == 0], drop=True)
                for field in (fields[member_id] for member_id in max_inputs)]
            first = inputs[0]
            if any(field.dims != first.dims or not field.coords.equals(first.coords) or
                   field.attrs.get("units") != first.attrs.get("units") for field in inputs[1:]):
                raise ValueError("ensemble members need matching grids and units for MAX")
            stack = xr.concat(inputs, dim=xr.IndexVariable("ensemble_member", list(max_inputs)))
            maximum = stack.max("ensemble_member", skipna=True)
            valid_count = stack.count("ensemble_member")
            valid_count.attrs = {"units": "1", "long_name": "Number of non-missing selected MAX inputs at each grid point"}
            maximum.attrs = {
                "units": "degC", "temperature_kind": "absolute", "standard_name": "air_temperature", "long_name": "Maximum 2 m temperature over selected realized inputs",
                "ensemble_statistic": "maximum", "ensemble_input_ids": json.dumps(max_inputs),
                "ensemble_requested_input_count": len(request.member_ids) + int(request.include_control_in_max),
                "ensemble_realized_input_count": len(max_inputs),
                "ensemble_missing_policy": request.missing_policy,
                "ensemble_include_control": int(request.include_control_in_max),
            }
            for source_key, target_key in [("field_identity", "source_field_identities"),
                                           ("source_reference", "source_references"),
                                           ("cedarkit_query_report", "source_query_reports")]:
                maximum.attrs[target_key] = json.dumps([json.loads(fields[mid].attrs[source_key])
                    if source_key in fields[mid].attrs else None for mid in max_inputs], sort_keys=True)
        return PreparedEnsemble(request, MappingProxyType(fields), tuple(realized), tuple(missing), control,
                                max_inputs if request.max_enabled else (), maximum, variant, reads, valid_count,
                                pd.Timestamp(start_time).isoformat(),
                                (pd.Timestamp(start_time) + pd.Timedelta(forecast_time)).isoformat(),
                                float(pd.Timedelta(forecast_time) / pd.Timedelta(hours=1)))


def select_ensemble_product(name: str) -> EnsembleT2MProduct | None:
    return EnsembleT2MProduct() if name == "cn.ens_t2m" else None
