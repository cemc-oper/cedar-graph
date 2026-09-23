"""All thirteen packaged CN recipes execute through the v3 workflow."""

import numpy as np
import pandas as pd
import pytest

from cedar_graph.recipes.workflow_product import select_workflow_product
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.plan import CompileContext


CASES = (
    ("bli_wind", {"wind_level": 850}, 3, ("cemc.bli:cn_fill", "cemc.bli:cn_line", "cemc.wind:cn")),
    ("cape_wind", {"wind_level": 850}, 3, ("cemc.cape:cn_fill", "cemc.cape:cn_line", "cemc.wind:cn")),
    ("cdbz", {}, 1, ("cemc.cdbz:cn",)),
    ("cin_wind", {"wind_level": 850}, 3, ("cemc.cin:cn", "cemc.wind:cn")),
    ("h_500_psl", {}, 2, ("cemc.psl:cn", "cemc.h_500:cn_dagpm")),
    ("h_500_wind_850", {}, 3, ("cemc.ws_850:cn", "cemc.h_500:cn_ws", "cemc.wind:cn")),
    ("kidx_wind", {"wind_level": 850}, 3, ("cemc.kidx:cn_fill", "cemc.kidx:cn_line", "cemc.wind:cn")),
    ("prep_24h", {}, 4, ("cemc.rain:cn_prep", "cemc.sf:cn", "cemc.rain_snow:cn")),
    ("rain_24h", {}, 2, ("cemc.rain:cn",)),
    ("rain_wind_10m", {"interval": "3h"}, 4, ("cemc.rain:cn_3h", "cemc.wind:cn")),
    ("rh2m", {}, 1, ("cemc.rh2m:cn",)),
    ("t2m", {}, 1, ("cemc.t2m:cn_summer",)),
    ("wind_10m", {}, 2, ("cemc.ws_10m:cn", "cemc.wind:cn")),
)

BAR_LABELS = {"h_500_psl": "hPa", "h_500_wind_850": "m/s", "cdbz": "dBZ",
              "t2m": "°C", "cape_wind": "J/kg", "cin_wind": "J/kg"}


@pytest.mark.parametrize("name,params,reads,styles", CASES)
def test_cn_recipe_compiles_executes_and_renders(name, params, reads, styles):
    product = select_workflow_product(f"cn.{name}")
    assert product is not None
    context = CompileContext(start_time="2024-07-01", forecast_time="24h", params=params)
    plan = product.compile(context)
    plots = plan.content.charts[0].plots
    assert plan.read_count == reads
    assert tuple(plot.style for plot in plots) == styles
    assert all(plot.targets == ("main" if plot.method == "barbs" else "all") for plot in plots)
    assert all(not bar.plots[0].plot.startswith("wind_") for bar in plan.content.colorbars)
    if name in BAR_LABELS:
        assert plan.content.colorbars[0].label == BAR_LABELS[name]

    source = MockDataSource(resolution=2)
    result = plan.execute(source, registry=product.discovery.ops)
    assert len(source.workflow_requests) == reads
    assert len(result.content.charts) == 1
    assert result.content.charts[0].titles[0].text
    panel = product.run(MockDataSource(resolution=2), context)
    try:
        assert len(panel.charts) == 1
        assert tuple(panel.charts["main"].layers[plots[0].id].results) == ("main", "south_china_sea")
    finally:
        panel.close()


@pytest.mark.parametrize("hours", (1, 3, 6, 12, 24))
def test_rain_wind_interval_selects_matching_variant_and_previous_read(hours):
    product = select_workflow_product("cn.rain_wind_10m")
    plan = product.compile(CompileContext(start_time="2024-07-01", forecast_time="24h",
                                          params={"interval": f"{hours}h"}))
    assert plan.content.charts[0].plots[0].style == f"cemc.rain:cn_{hours}h"
    assert plan.content.charts[0].titles[0].text == f"surface cumulated precipitation: {24-hours:03d}-024h"
    source = MockDataSource(resolution=2)
    result = plan.execute(source, registry=product.discovery.ops)
    assert result.outputs["rain"].attrs["units"] == "mm"
    assert result.outputs["rain"].attrs["accumulation_hours"] == hours
    rain_times = {request.key.forecast_time for request in source.workflow_requests
                  if request.key.parameter_id == "cedarkit.rain"}
    assert rain_times == {pd.Timedelta("24h").isoformat(), pd.Timedelta(hours=24-hours).isoformat()}
    assert float(result.outputs["rain"].max()) > 0


def test_height_pressure_snow_and_wind_numeric_units():
    context = CompileContext(start_time="2024-07-01", forecast_time="24h")
    height = select_workflow_product("cn.h_500_psl")
    height_data = height.compile(context).execute(MockDataSource(resolution=2), registry=height.discovery.ops)
    assert height_data.outputs["h_500"].attrs["units"] == "dagpm"
    assert height_data.outputs["psl"].attrs["units"] == "hPa"
    assert 500 < float(height_data.outputs["h_500"].mean()) < 650
    assert 970 < float(height_data.outputs["psl"].mean()) < 1050

    prep = select_workflow_product("cn.prep_24h")
    prep_data = prep.compile(context).execute(MockDataSource(resolution=2), registry=prep.discovery.ops)
    assert prep_data.outputs["snow_total"].attrs == {"units": "mm", "accumulation_hours": 24.0}
    assert all(prep_data.outputs[name].attrs["units"] == "mm" for name in ("rain", "snow", "rain_snow"))
    assert any(np.isfinite(prep_data.outputs[name]).any() for name in ("rain", "snow", "rain_snow"))

    wind = select_workflow_product("cn.wind_10m")
    wind_data = wind.compile(context).execute(MockDataSource(resolution=2), registry=wind.discovery.ops)
    np.testing.assert_allclose(wind_data.outputs["ws_10m"],
                               np.hypot(wind_data.outputs["u_10m"], wind_data.outputs["v_10m"]) * 0.4)
    assert wind_data.outputs["ws_10m"].attrs["units"] == "m/s"
