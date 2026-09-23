"""Thin bridge binding cedar-graph field requirements to reki sources."""
from __future__ import annotations
from dataclasses import dataclass, replace
import json
import re
from time import perf_counter
from typing import Any, Mapping

import xarray as xr
import pandas as pd
import reki

from cedarkit.plots.workflow.plan.model import BoundFieldRequest, FieldRequest


@dataclass(frozen=True)
class ProviderTrace:
    """Public, credential-free evidence for one provider request."""

    node_id: str
    dataset_id: str | None
    catalog_origin: str | None
    provider: str
    parameter_id: str
    external_parameter: str | None
    level_type: Any
    level: Any
    start_time: str | None
    forecast_time: str | None
    status: str
    duration_seconds: float
    error_code: str | None = None

class RekiProvider:
    """Load strict reki fields from a reusable :class:`reki.SourceSpec`."""
    def __init__(self, source_spec: reki.SourceSpec | Any, *,
                 region: Mapping[str, Any] | None = None):
        """Create a provider from a SourceSpec or catalog ResolvedDataset."""
        self.dataset_id = None
        self.catalog_origin = None
        if hasattr(source_spec, "source") and hasattr(source_spec, "record"):
            self.dataset_id = source_spec.record.dataset_id
            self.catalog_origin = source_spec.origin
            source_spec = source_spec.source
        if not isinstance(source_spec, reki.SourceSpec):
            raise TypeError("source_spec must be a reki.SourceSpec")
        self.source_spec = source_spec
        self.region = None if region is None else dict(region)
        self.trace: list[ProviderTrace] = []
        self._field_cache: dict[tuple[Any, ...], xr.DataArray | None] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._closed = False

    def close(self) -> None:
        """Release task-owned cached arrays and traces; leave the source alone."""
        self._field_cache.clear()
        self.trace.clear()
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("provider is closed")

    @property
    def cache_info(self) -> Mapping[str, int]:
        """Counters and entries for this provider's task-local field cache."""
        return {"hits": self._cache_hits, "misses": self._cache_misses, "entries": len(self._field_cache)}

    @staticmethod
    def _field_cache_key(query, start_time, forecast_time, required, parameter_id):
        query_key = json.dumps({
            "parameter": query.parameter, "level_type": query.level_type,
            "level": query.level, "step_type": query.step_type,
            "time_range": query.time_range, "member": query.member,
            "extra": dict(query.extra),
        }, sort_keys=True, default=str)
        return (query_key, str(start_time), str(forecast_time), required, parameter_id)

    def _capability(self):
        """Read the source-declared capability without mutating the source."""
        return reki.source_capability(self.source_spec)

    @staticmethod
    def _bindings(*, start_time=None, forecast_time=None):
        return {key: value for key, value in {
            "start_time": start_time, "forecast_time": forecast_time,
        }.items() if value is not None}

    def _selectable_binding(self, query, *, start_time=None, forecast_time=None):
        """Bind a mounted ensemble member to both its file and GRIB field."""
        bindings = self._bindings(start_time=start_time, forecast_time=forecast_time)
        if self.source_spec.name != "local" or query.member is None:
            return bindings, query
        member = query.member
        if isinstance(member, bool) or not (isinstance(member, int) and member >= 0
                                             or isinstance(member, str) and re.fullmatch(r"m?\d+", member)):
            raise ValueError(f"local ensemble member must be a non-negative number or mNNN ID: {member!r}")
        number = int(member.lstrip("m")) if isinstance(member, str) else member
        bindings["number"] = number
        return bindings, replace(query, member=number)

    @staticmethod
    def _request_times(key):
        """Decode v3 request times for the reki source."""
        start = pd.Timestamp(key.start_time) if key.start_time is not None else None
        if key.forecast_time is None:
            forecast = None
        else:
            try:
                forecast = pd.Timedelta(key.forecast_time)
            except (TypeError, ValueError):
                forecast = pd.Timestamp(key.forecast_time)
        return start, forecast

    def _append_trace(self, request: BoundFieldRequest, *, status: str,
                      duration: float, external_parameter: str | None = None,
                      error_code: str | None = None) -> None:
        key = request.key
        start_time, forecast_time = self._request_times(key)
        self.trace.append(ProviderTrace(
            node_id=request.node_id, dataset_id=self.dataset_id,
            catalog_origin=self.catalog_origin, provider=self.source_spec.name,
            parameter_id=key.parameter_id, external_parameter=external_parameter,
            level_type=key.query.level_type, level=key.query.level,
            start_time=None if start_time is None else str(start_time),
            forecast_time=None if forecast_time is None else str(forecast_time),
            status=status, duration_seconds=duration, error_code=error_code,
        ))

    def load(self, query: reki.FieldQuery, *, start_time=None,
             forecast_time=None, required: bool = True, parameter_id: str | None = None):
        self._ensure_open()
        if not isinstance(query, reki.FieldQuery):
            raise TypeError("query must be a reki.FieldQuery")
        cache_key = self._field_cache_key(query, start_time, forecast_time, required, parameter_id)
        if cache_key in self._field_cache:
            self._cache_hits += 1
            value = self._field_cache[cache_key]
            return None if value is None else value.copy(deep=False)
        self._cache_misses += 1
        capability = self._capability()
        if capability is not None and capability.direct_result:
            if parameter_id is None:
                raise ValueError("a stable parameter_id is required for a direct-result source")
            request = BoundFieldRequest(
                node_id="legacy-load",
                key=FieldRequest(
                    provider_slot="default", parameter_id=parameter_id,
                    query=query,
                    start_time=None if start_time is None else str(start_time),
                    forecast_time=None if forecast_time is None else str(forecast_time),
                    cardinality="one" if required else "first",
                ),
                origin="legacy FieldInfo adapter",
            )
            value = self._fetch_direct(request)
            self._field_cache[cache_key] = value
            return value.copy(deep=False)
        bindings, selected_query = self._selectable_binding(
            query, start_time=start_time, forecast_time=forecast_time)
        reader = reki.from_source(self.source_spec, **bindings)
        selected = reader.sel(selected_query)
        field = selected.one() if required else selected.one_or_none()
        value = None if field is None else field.to_xarray()
        self._field_cache[cache_key] = value
        return None if value is None else value.copy(deep=False)

    def _load_many(self, queries, *, start_time=None, forecast_time=None,
                   required=True):
        """Stage-3 prototype; recipe execution does not call this yet."""
        if not all(isinstance(query, reki.FieldQuery) for query in queries):
            raise TypeError("queries must contain FieldQuery objects")
        bindings = self._bindings(start_time=start_time, forecast_time=forecast_time)
        reader = reki.from_source(self.source_spec, **bindings)
        if not reader.capabilities.fetch_many:
            raise RuntimeError("configured reki reader does not support batch fields")
        mode = "one" if required else "one_or_none"
        fields = reader.fetch_many(queries, cardinality=mode)
        return [None if field is None else field.to_xarray() for field in fields]

    # WorkflowPlan provider contract --------------------------------------------
    def fetch(self, request: BoundFieldRequest):
        """Fetch one compiled request using its concrete time binding."""
        self._ensure_open()
        capability = self._capability()
        if capability is not None and capability.direct_result:
            start_time, forecast_time = self._request_times(request.key)
            cache_key = self._field_cache_key(request.key.query, start_time, forecast_time,
                                              request.key.cardinality != "all", request.key.parameter_id)
            if cache_key in self._field_cache:
                self._cache_hits += 1
                value = self._field_cache[cache_key]
                self._append_trace(request, status="cached", duration=0)
                return None if value is None else value.copy(deep=False)
            self._cache_misses += 1
            value = self._fetch_direct(request)
            self._field_cache[cache_key] = value
            return value.copy(deep=False)
        return self._fetch_selectable(request)

    def _fetch_selectable(self, request: BoundFieldRequest):
        started = perf_counter()
        start_time, forecast_time = self._request_times(request.key)
        cache_key = self._field_cache_key(request.key.query, start_time, forecast_time,
                                          request.key.cardinality != "all", request.key.parameter_id)
        cached = cache_key in self._field_cache
        try:
            value = self.load(
                request.key.query,
                start_time=start_time,
                forecast_time=forecast_time,
                required=request.key.cardinality != "all",
                parameter_id=request.key.parameter_id,
            )
        except Exception as exc:
            self._append_trace(request, status="error", duration=perf_counter() - started,
                               error_code=getattr(exc, "code", type(exc).__name__))
            raise
        self._append_trace(request, status="cached" if cached else ("missing" if value is None else "ok"),
                           duration=perf_counter() - started)
        return value

    def _fetch_direct(self, request: BoundFieldRequest):
        """Bind a high-level request before source construction; never select it."""
        started = perf_counter()
        start_time, forecast_time = self._request_times(request.key)
        try:
            bound = reki.bind_cmadaas_request(
                self.source_spec, parameter_id=request.key.parameter_id,
                query=request.key.query,
                start_time=start_time,
                forecast_time=forecast_time,
                member=request.key.query.member,
                region=self.region,
            )
            result = reki.from_source(self.source_spec, **bound.dynamic_source_kwargs()).to_xarray()
            if not isinstance(result, xr.DataArray):
                raise TypeError("CMADaaS model_grid must return one xarray.DataArray")
            result = reki.normalize_data_array(result, source=self.source_spec)
            reki.validate_data_array(result, mode="raise")
            result = result.rename(request.key.parameter_id)
            result.attrs = dict(result.attrs)
            result.attrs["cmadaas_parameter"] = bound.parameter
        except Exception as exc:
            self._append_trace(request, status="error", duration=perf_counter() - started,
                               error_code=getattr(exc, "code", type(exc).__name__))
            raise
        self._append_trace(request, status="ok", duration=perf_counter() - started,
                           external_parameter=bound.parameter)
        return result

    def fetch_many(self, requests):
        """Fetch in order through the same cache and trace path as fetch."""
        requests = tuple(requests)
        return [self.fetch(request) for request in requests]

    def check_many(self, requests):
        """Check metadata when supported; direct-result sources are unknown."""
        self._ensure_open()
        capability = self._capability()
        if capability is not None and not capability.metadata_only:
            return ["unknown" for _ in requests]
        result = []
        for request in requests:
            start_time, forecast_time = self._request_times(request.key)
            kwargs, selected_query = self._selectable_binding(
                request.key.query, start_time=start_time, forecast_time=forecast_time)
            try:
                reader = reki.from_source(self.source_spec, **kwargs)
                selected = reader.sel(selected_query)
                # ``one_or_none`` is the strict metadata/cardinality boundary;
                # it does not call ``to_xarray`` or decode values.
                result.append("available" if selected.one_or_none() is not None else "missing")
            except Exception as exc:
                result.append("provider_error")
        return result
