"""First migrated product uses v3 requests, units and presentation."""

import numpy as np
import pandas as pd
import reki
import xarray as xr

from cedar_graph.data import RekiProvider
from cedar_graph.data.field_info import field_info_from_parameter
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.plan import CompileContext


def test_t2m_product_selects_seasonal_style_and_converts_once():
    product = select_workflow_product("cn.t2m")
    assert product is not None
    summer = product.compile(CompileContext(start_time="2024-07-01", forecast_time="24h",
                                             params={"style_variant": "cn_summer"}))
    winter = product.compile(CompileContext(start_time="2024-01-01", forecast_time="24h",
                                             params={"style_variant": "cn_winter"}))
    assert summer.read_count == winter.read_count == 1
    assert summer.content.charts[0].plots[0].style == "cemc.t2m:cn_summer"
    assert winter.content.charts[0].plots[0].style == "cemc.t2m:cn_winter"
    assert len(summer.content.charts[0].plots) == 1
    assert summer.content.charts[0].plots[0].targets == "all"
    assert summer.content.colorbars[0].label == "°C"
    assert summer.content.charts[0].titles[0].text == "2m Temperature (°C)"

    provider = MockDataSource(resolution=2)
    result = summer.execute(provider, registry=product.discovery.ops)
    output = result.outputs["temperature"]
    assert len(provider.workflow_requests) == 1
    assert provider.workflow_requests[0].key.parameter_id == "cedarkit.t2m"
    assert output.attrs["units"] == "degC"
    source = provider.retrieve(field_info_from_parameter("cedarkit.t2m", name="t2m"),
                               pd.Timestamp("2024-07-01"), pd.Timedelta("24h"))
    np.testing.assert_allclose(output.values, source.values - 273.15)

    panel = product.run(MockDataSource(resolution=2), CompileContext(
        start_time="2024-07-01", forecast_time="24h", params={"style_variant": "cn_summer"}))
    try:
        assert tuple(panel.charts["main"].layers["temperature"].results) == ("main", "south_china_sea")
    finally:
        panel.close()


def test_reki_provider_accepts_v3_bound_request(monkeypatch):
    field = xr.DataArray(np.full((2, 2), 273.15), dims=("y", "x"), attrs={"units": "K"})
    calls = []

    class Reader:
        def sel(self, query):
            calls.append(query)
            return self

        def one(self):
            return self

        def to_xarray(self):
            return field

    monkeypatch.setattr(reki, "source_capability", lambda source: None)
    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: Reader())
    product = select_workflow_product("cn.t2m")
    plan = product.compile(CompileContext(start_time="2024-07-01", forecast_time="24h"))
    provider = RekiProvider(reki.SourceSpec("local"))
    result = plan.execute(provider, registry=product.discovery.ops)
    assert float(result.outputs["temperature"].values[0, 0]) == 0.0
    assert len(calls) == len(provider.trace) == 1
    assert provider.trace[0].node_id.startswith("read:")
    assert provider.trace[0].parameter_id == "cedarkit.t2m"
