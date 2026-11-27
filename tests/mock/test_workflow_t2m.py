"""First migrated product uses v3 requests, units and presentation."""

import numpy as np
import pandas as pd
import reki
import xarray as xr

from cedar_graph.data import RekiProvider
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
    assert not summer.content.colorbars
    assert summer.content.charts[0].colorbars[0].label == "°C"
    assert {title.id: title.text for title in summer.content.charts[0].titles} == {
        "heading": "2 m Temperature (°C)",
        "model": "CMA-GFS",
        "init": "Init 2024070100 UTC\n2024070108 CST",
        "lead": "+24 h",
        "valid": "Valid 2024070200 UTC\n2024070208 CST",
    }

    provider = MockDataSource(resolution=2)
    result = summer.execute(provider, registry=product.discovery.ops)
    output = result.outputs["temperature"]
    assert len(provider.workflow_requests) == 1
    assert provider.workflow_requests[0].key.parameter_id == "cedarkit.t2m"
    assert output.attrs["units"] == "degC"
    source = provider.field("cedarkit.t2m", name="t2m",
                            start_time=pd.Timestamp("2024-07-01"),
                            forecast_time=pd.Timedelta("24h"))
    np.testing.assert_allclose(output.values, source.values - 273.15)

    panel = product.run(MockDataSource(resolution=2), CompileContext(
        start_time="2024-07-01", forecast_time="24h", params={"style_variant": "cn_summer"}))
    try:
        assert tuple(panel.charts["main"].layers["temperature"].results) == ("main", "south_china_sea")
    finally:
        panel.close()


def test_reki_provider_accepts_v3_bound_request(tmp_path):
    from .test_public_query_provider import _fixture
    source, plan, _, product = _fixture(tmp_path)
    with RekiProvider(source) as provider:
        result = plan.execute(provider, registry=product.discovery.ops)
        np.testing.assert_allclose(result.outputs["temperature"].values, np.arange(280.,292.).reshape(3,4)-273.15)
        assert len(provider.trace)==1
        assert provider.trace[0].node_id.startswith("read:")
        assert provider.trace[0].parameter_id=="cedarkit.t2m"
