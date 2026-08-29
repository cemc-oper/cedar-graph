"""Thin bridge binding cedar-graph field requirements to reki sources."""
from __future__ import annotations
from typing import Optional
import reki

from cedarkit.plots.plan.provider import BoundFieldRequest

class RekiProvider:
    """Load strict reki fields from a reusable :class:`reki.SourceSpec`."""
    def __init__(self, source_spec: reki.SourceSpec):
        if not isinstance(source_spec, reki.SourceSpec):
            raise TypeError("source_spec must be a reki.SourceSpec")
        self.source_spec = source_spec

    def load(self, query: reki.FieldQuery, *, start_time=None,
             forecast_time=None, required: bool = True):
        if not isinstance(query, reki.FieldQuery):
            raise TypeError("query must be a reki.FieldQuery")
        bindings = {k: v for k, v in {
            "start_time": start_time, "forecast_time": forecast_time,
        }.items() if v is not None}
        reader = reki.from_source(self.source_spec, **bindings)
        selected = reader.sel(query)
        field = selected.one() if required else selected.one_or_none()
        return None if field is None else field.to_xarray()

    def _load_many(self, queries, *, start_time=None, forecast_time=None,
                   required=True):
        """Stage-3 prototype; recipe execution does not call this yet."""
        if not all(isinstance(query, reki.FieldQuery) for query in queries):
            raise TypeError("queries must contain FieldQuery objects")
        bindings = {key: value for key, value in {
            "start_time": start_time, "forecast_time": forecast_time,
        }.items() if value is not None}
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
        return self.load(
            request.key.query,
            start_time=request.key.time_binding.start_time,
            forecast_time=request.key.time_binding.forecast_time,
            required=request.key.cardinality != "all",
        )

    def fetch_many(self, requests):
        """Batch equivalent-time plan reads while preserving request order."""
        requests = tuple(requests)
        if not requests:
            return []
        first = requests[0]
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
        """Check cardinality through reki metadata selection without decoding values."""
        result = []
        for request in requests:
            binding = request.key.time_binding
            kwargs = {key: value for key, value in {
                "start_time": binding.start_time,
                "forecast_time": binding.forecast_time,
            }.items() if value is not None}
            try:
                reader = reki.from_source(self.source_spec, **kwargs)
                selected = reader.sel(request.key.query)
                # ``one_or_none`` is the strict metadata/cardinality boundary;
                # it does not call ``to_xarray`` or decode values.
                result.append("available" if selected.one_or_none() is not None else "missing")
            except Exception as exc:
                result.append("provider_error")
        return result
