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
