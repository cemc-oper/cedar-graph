"""Thin bridge binding cedar-graph field requirements to reki sources."""
from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Mapping

import xarray as xr
import reki

from cedarkit.plots.plan.nodes import RequestKey, TimeBinding
from cedarkit.plots.plan.provider import BoundFieldRequest


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

    def _capability(self):
        """Read the source-declared capability without mutating the source."""
        return reki.source_capability(self.source_spec)

    @staticmethod
    def _bindings(*, start_time=None, forecast_time=None):
        return {key: value for key, value in {
            "start_time": start_time, "forecast_time": forecast_time,
        }.items() if value is not None}

    def _append_trace(self, request: BoundFieldRequest, *, status: str,
                      duration: float, external_parameter: str | None = None,
                      error_code: str | None = None) -> None:
        key = request.key
        binding = key.time_binding
        self.trace.append(ProviderTrace(
            node_id=request.node_id, dataset_id=self.dataset_id,
            catalog_origin=self.catalog_origin, provider=self.source_spec.name,
            parameter_id=key.parameter_id, external_parameter=external_parameter,
            level_type=key.query.level_type, level=key.query.level,
            start_time=binding.start_time, forecast_time=binding.forecast_time,
            status=status, duration_seconds=duration, error_code=error_code,
        ))

    def load(self, query: reki.FieldQuery, *, start_time=None,
             forecast_time=None, required: bool = True, parameter_id: str | None = None):
        if not isinstance(query, reki.FieldQuery):
            raise TypeError("query must be a reki.FieldQuery")
        capability = self._capability()
        if capability is not None and capability.direct_result:
            if parameter_id is None:
                raise ValueError("a stable parameter_id is required for a direct-result source")
            request = BoundFieldRequest(
                node_id="legacy-load",
                key=RequestKey(
                    provider_slot="default", parameter_id=parameter_id,
                    query=query,
                    time_binding=TimeBinding(start_time, forecast_time),
                    cardinality="one" if required else "first",
                ),
                origin="legacy FieldInfo adapter",
            )
            return self._fetch_direct(request)
        bindings = self._bindings(start_time=start_time, forecast_time=forecast_time)
        reader = reki.from_source(self.source_spec, **bindings)
        selected = reader.sel(query)
        field = selected.one() if required else selected.one_or_none()
        return None if field is None else field.to_xarray()

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

    # PlotPlan provider contract -------------------------------------------------
    # The source binding remains here, rather than in recipes or plans.
    def fetch(self, request: BoundFieldRequest):
        """Fetch one compiled request using its concrete time binding."""
        capability = self._capability()
        if capability is not None and capability.direct_result:
            return self._fetch_direct(request)
        return self._fetch_selectable(request)

    def _fetch_selectable(self, request: BoundFieldRequest):
        started = perf_counter()
        try:
            value = self.load(
                request.key.query,
                start_time=request.key.time_binding.start_time,
                forecast_time=request.key.time_binding.forecast_time,
                required=request.key.cardinality != "all",
                parameter_id=request.key.parameter_id,
            )
        except Exception as exc:
            self._append_trace(request, status="error", duration=perf_counter() - started,
                               error_code=getattr(exc, "code", type(exc).__name__))
            raise
        self._append_trace(request, status="missing" if value is None else "ok",
                           duration=perf_counter() - started)
        return value

    def _fetch_direct(self, request: BoundFieldRequest):
        """Bind a high-level request before source construction; never select it."""
        started = perf_counter()
        try:
            bound = reki.bind_cmadaas_request(
                self.source_spec, parameter_id=request.key.parameter_id,
                query=request.key.query,
                start_time=request.key.time_binding.start_time,
                forecast_time=request.key.time_binding.forecast_time,
                member=request.key.time_binding.member,
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
        """Batch equivalent-time plan reads while preserving request order."""
        requests = tuple(requests)
        if not requests:
            return []
        first = requests[0]
        capability = self._capability()
        if capability is not None and capability.direct_result:
            # MUSIC has no equivalent grid batch API.  Keep input order and
            # fail at the first required request exactly as repeated fetch().
            return [self.fetch(request) for request in requests]
        if any(request.key.time_binding != first.key.time_binding for request in requests):
            # The executor normally groups these; retain a safe provider-level
            # fallback for direct callers.
            return [self.fetch(request) for request in requests]
        return self._load_many(
            [request.key.query for request in requests],
            start_time=first.key.time_binding.start_time,
            forecast_time=first.key.time_binding.forecast_time,
            required=first.key.cardinality != "all",
        )

    def check_many(self, requests):
        """Check metadata when supported; direct-result sources are unknown."""
        capability = self._capability()
        if capability is not None and not capability.metadata_only:
            return ["unknown" for _ in requests]
        result = []
        for request in requests:
            binding = request.key.time_binding
            kwargs = self._bindings(start_time=binding.start_time, forecast_time=binding.forecast_time)
            try:
                reader = reki.from_source(self.source_spec, **kwargs)
                selected = reader.sel(request.key.query)
                # ``one_or_none`` is the strict metadata/cardinality boundary;
                # it does not call ``to_xarray`` or decode values.
                result.append("available" if selected.one_or_none() is not None else "missing")
            except Exception as exc:
                result.append("provider_error")
        return result
