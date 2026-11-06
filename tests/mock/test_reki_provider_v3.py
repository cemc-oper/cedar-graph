"""Source-neutral v3 requests through selectable and CMADaaS providers."""

import pandas as pd
import reki
import pytest
from cedarkit_query import Query, QueryError
import xarray as xr
from dataclasses import replace

from cedar_graph.data import RekiProvider
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedarkit.plots.workflow.plan.model import BoundFieldRequest
from cedarkit.plots.workflow.plan import CompileContext


def _request(node_id="read.t2m"):
    plan = select_workflow_product("cn.t2m").compile(CompileContext(
        start_time="2026-07-16", forecast_time="24h", params={"style_variant": "cn_summer"}))
    key = next(node.request for node in plan.nodes if node.request is not None)
    return BoundFieldRequest(node_id, key, "test")


def test_selectable_provider_uses_v3_query_and_metadata_check(monkeypatch):
    field = xr.DataArray([[273.15]], dims=("latitude", "longitude"),
                         coords={"latitude": [30.0], "longitude": [110.0]}, attrs={"units": "K"})
    calls = []

    class Reader:
        def sel(self, query):
            calls.append(query)
            return self

        def one(self):
            return self

        def one_or_none(self):
            return self

        def to_xarray(self):
            return field

    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: Reader())
    provider = RekiProvider(reki.SourceSpec("local", args=("fixture",)))
    try:
        request = _request()
        assert provider.check_many((request,)) == ["available"]
        values = provider.fetch_many((request, request))
        assert len(values) == 2 and values[0].identical(values[1])
        assert calls[0].parameter == request.key.parameter_id
        assert isinstance(calls[0], reki.FieldQuery)
        assert provider.cache_info == {"hits": 1, "misses": 1, "entries": 1}
        assert [item.status for item in provider.trace] == ["ok", "cached"]
    finally:
        provider.close()
    assert provider.trace == []


def test_legacy_provider_keeps_unbound_time_behavior(monkeypatch):
    bindings = []
    field = xr.DataArray([[273.15]], dims=("latitude", "longitude"),
                         coords={"latitude": [30.0], "longitude": [110.0]}, attrs={"units": "K"})

    class Reader:
        def sel(self, query):
            return self

        def one(self):
            return self

        def to_xarray(self):
            return field

    monkeypatch.setattr(reki, "from_source", lambda spec, **kwargs: bindings.append(kwargs) or Reader())
    request = _request()
    assert request.key.start_time == "2026-07-16T00:00:00Z"
    request = replace(request, key=replace(request.key, start_time=None, forecast_time=None))
    with RekiProvider(reki.SourceSpec("local", args=("fixture",))) as provider:
        assert provider.fetch(request).identical(field)
        assert provider.trace[0].start_time is None
        assert provider.trace[0].forecast_time is None
    assert bindings == [{}]


def test_removed_legacy_cmadaas_binding_requires_current_source_declaration(monkeypatch):
    """Removed reki bind APIs are not recreated as a second query protocol."""
    from types import SimpleNamespace
    provider = RekiProvider(reki.SourceSpec("cmadaas", kwargs={"kind": "model_grid"}))
    monkeypatch.setattr(provider, "_capability", lambda: SimpleNamespace(direct_result=True))
    with provider:
        with pytest.raises(QueryError, match="public source declaration") as caught:
            provider.fetch(_request())
        assert caught.value.code == "unsupported"
        assert provider.trace[-1].error_code == "unsupported"


def test_mounted_ensemble_member_binds_file_number_and_grib_member(monkeypatch):
    field = xr.DataArray([[273.15]], dims=("latitude", "longitude"),
                         coords={"latitude": [30.0], "longitude": [110.0]}, attrs={"units": "K"})
    calls = []

    class Reader:
        def sel(self, query):
            calls.append(("query", query))
            return self

        def one(self):
            return self

        def to_xarray(self):
            return field

    monkeypatch.setattr(reki, "from_source", lambda spec, **kwargs: calls.append(("source", kwargs)) or Reader())
    provider = RekiProvider(reki.SourceSpec("local", args=("cma_geps/grib2/orig",)))
    try:
        from dataclasses import replace
        request = _request()
        query = Query({**request.key.query.to_dict(), "member": 3})
        request = replace(request, key=replace(request.key, query=query))
        result = provider.fetch(request)
        assert result.identical(field)
        assert calls[0][1]["number"] == 3
        assert calls[1][1].member == 3
        assert request.key.query.member == 3
    finally:
        provider.close()
