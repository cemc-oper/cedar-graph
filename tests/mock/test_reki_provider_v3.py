"""Source-neutral v3 requests through selectable and CMADaaS providers."""

import pandas as pd
import reki
import xarray as xr

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
        assert calls[0] == request.key.query
        assert provider.cache_info == {"hits": 1, "misses": 1, "entries": 1}
        assert [item.status for item in provider.trace] == ["ok", "cached"]
    finally:
        provider.close()


def test_cmadaas_provider_binds_v3_request_and_region_without_select(monkeypatch):
    dataset = reki.load_catalog(plugins=False, user=False).resolve("CMA-GFS-CMADaaS")
    field = xr.DataArray([[273.15]], dims=("latitude", "longitude"),
                         coords={"latitude": [30.0], "longitude": [110.0]}, attrs={"units": "K"})
    calls = []

    class DirectReader:
        def sel(self, query):
            raise AssertionError("direct-result source must not select a field")

        def to_xarray(self):
            return field

    monkeypatch.setattr(reki, "from_source", lambda spec, **kwargs: calls.append(kwargs) or DirectReader())
    region = {"type": "rect", "min_latitude": 20.0}
    provider = RekiProvider(dataset, region=region)
    try:
        request = _request("first")
        assert provider.check_many((request,)) == ["unknown"]
        result = provider.fetch(request)
        assert result.name == "cedarkit.t2m"
        assert result.attrs["cmadaas_parameter"] == "TEM"
        assert calls[0]["region"] == region
        assert calls[0]["start_time"] == pd.Timestamp("2026-07-16", tz="UTC")
        assert calls[0]["forecast_time"] == pd.Timedelta("24h")
        assert provider.trace[0].node_id == "first"
        assert provider.trace[0].dataset_id == dataset.record.dataset_id
        assert provider.trace[0].catalog_origin == dataset.origin
        assert provider.trace[0].external_parameter == "TEM"
    finally:
        provider.close()
