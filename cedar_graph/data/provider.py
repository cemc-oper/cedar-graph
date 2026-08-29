"""Thin bridge binding cedar-graph field requirements to reki sources."""
from __future__ import annotations
from typing import Optional
import reki

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
