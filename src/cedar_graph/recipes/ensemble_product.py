"""Caller-owned EnsCN charts backed by per-member v3 data plans."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Mapping

import cartopy.crs as ccrs
import pandas as pd
import xarray as xr

from cedarkit.plots import Panel
from cedarkit.plots.config import BasemapSpec, Cell, Rect
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


@dataclass(frozen=True)
class EnsembleRequest:
    member_ids: tuple[str, ...]
    control_id: str | None = None
    include_control_in_max: bool = False
    missing_policy: Literal["error", "skip"] = "error"
    max_enabled: bool = True
    columns: int = 5
    style_variant: Literal["cn_summer", "cn_winter"] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.member_ids, (list, tuple)):
            raise ValueError("member_ids must be a list or tuple")
        ids = tuple(_member_id(value) for value in self.member_ids)
        if not ids or len(set(ids)) != len(ids):
            raise ValueError("member_ids must be non-empty and unique")
        object.__setattr__(self, "member_ids", ids)
        if self.control_id is not None:
            control = _member_id(self.control_id)
            if control in ids:
                raise ValueError("control_id must be distinct from member_ids")
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
            styles = get_default_registry()
            layers = []
            ordered = ([self.realized_control_id] if self.realized_control_id else []) + list(self.realized_member_ids)
            if self.max_field is not None:
                ordered.append("max")
            for chart_id in ordered:
                role = "control" if chart_id == self.realized_control_id else ("max" if chart_id == "max" else "member")
                field = self.max_field if chart_id == "max" else self.fields[chart_id]
                chart = panel.add_chart(id=chart_id, role=role)
                chart.set_title("CTL" if role == "control" else ("MAX" if role == "max" else chart_id))
                style = styles.get_style(f"cemc.t2m:{self.style_variant}", data=field)
                layers.append(chart.contourf(field, style=style, id="temperature",
                                             data_crs=ccrs.PlateCarree(), subplots="main"))
            panel.colorbar(tuple(layers), id="ens_cn_colorbar", label="°C", subplots="main")
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
            params={"member_id": member_id, "style_variant": variant}, cardinality="all"),
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
            fields[member_id] = result.outputs["temperature"]
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
        if request.max_enabled:
            inputs = [fields[member_id] for member_id in max_inputs]
            first = inputs[0]
            if any(field.dims != first.dims or not field.coords.equals(first.coords) or
                   field.attrs.get("units") != first.attrs.get("units") for field in inputs[1:]):
                raise ValueError("ensemble members need matching grids and units for MAX")
            maximum = xr.concat(inputs, dim=xr.IndexVariable("ensemble_member", list(max_inputs))).max(
                "ensemble_member", skipna=True)
            maximum.attrs = dict(first.attrs)
        return PreparedEnsemble(request, MappingProxyType(fields), tuple(realized), tuple(missing), control,
                                max_inputs if request.max_enabled else (), maximum, variant, reads)


def select_ensemble_product(name: str) -> EnsembleT2MProduct | None:
    return EnsembleT2MProduct() if name == "cn.ens_t2m" else None
