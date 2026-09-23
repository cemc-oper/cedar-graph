"""Former Python products use the shared workflow for data and content."""

import numpy as np
import pandas as pd
import pytest

from cedarkit.comp.smooth import smth9
from cedar_graph.data.field_info import field_info_from_parameter
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.plan import CompileContext
from cedarkit.plots.workflow.runtime import PlanExecutionError


CASES = (
    ("div_wind", {"div_level": 850, "wind_level": 850}, 3,
     ("cemc.div:cn_fill", "cemc.div:cn_line", "cemc.wind:cn")),
    ("pte_wind", {"wind_level": 850, "pte_first_level": 500, "pte_second_level": 850}, 4,
     ("cemc.pte_diff:cn_fill", "cemc.pte_diff:cn_line", "cemc.wind:cn")),
    ("qv_div", {"level": 850}, 1, ("cemc.qdiv:cn_fill", "cemc.qdiv:cn_line")),
    ("shr", {"first_level": 3000, "second_level": 0}, 1,
     ("cemc.shr:cn_fill", "cemc.shr:cn_line")),
    ("t_dew_t", {"level": 850}, 2,
     ("cemc.t_dew_t:cn_fill", "cemc.t_dew_t:cn_line", "cemc.t_dew_t:cn_t")),
)


def _context(params):
    return CompileContext(start_time="2024-07-01", forecast_time="24h", params=params)


def _raw(source, parameter, name, level, level_type=100):
    info = field_info_from_parameter(parameter, name=name)
    info.level, info.level_type = level, level_type
    return source.retrieve(info, pd.Timestamp("2024-07-01"), pd.Timedelta("24h"))


@pytest.mark.parametrize("name,params,reads,styles", CASES)
def test_python_product_compiles_executes_and_renders(name, params, reads, styles):
    product = select_workflow_product(f"cn.{name}.default")
    assert product is not None
    plan = product.compile(_context(params))
    plots = plan.content.charts[0].plots
    assert plan.read_count == reads
    assert tuple(plot.style for plot in plots) == styles
    assert all(plot.targets == ("main" if plot.method == "barbs" else "all") for plot in plots)
    assert len(plan.content.colorbars) == 1
    source = MockDataSource(resolution=2)
    result = plan.execute(source, registry=product.discovery.ops)
    assert len(source.workflow_requests) == reads
    assert result.content.charts[0].titles[0].text
    panel = product.run(MockDataSource(resolution=2), _context(params))
    try:
        assert tuple(panel.charts["main"].layers[plots[0].id].results) == ("main", "south_china_sea")
    finally:
        panel.close()


def test_divergence_scaling_smoothing_and_pressure_levels():
    product = select_workflow_product("cn.div_wind.default")
    source = MockDataSource(resolution=2)
    plan = product.compile(_context({"div_level": 700, "wind_level": 850}))
    result = plan.execute(source, registry=product.discovery.ops)
    raw = _raw(source, "cedarkit.div", "div", 700)
    expected = smth9(smth9(raw.values, 0.5, -0.25, False), 0.5, -0.25, False) * 1e5
    np.testing.assert_allclose(result.outputs["div"].values, expected)
    assert result.outputs["div"].attrs["units"] == "10^-5 s^-1"
    requests = {request.key.parameter_id: request.key.query.extra["first_level"]
                for request in source.workflow_requests}
    assert requests == {"cedarkit.div": 700.0, "cedarkit.u": 850.0, "cedarkit.v": 850.0}


def test_pte_two_levels_and_temperature_difference():
    product = select_workflow_product("cn.pte_wind.default")
    source = MockDataSource(resolution=2)
    result = product.compile(_context({"wind_level": 850, "pte_first_level": 500,
                                       "pte_second_level": 850})).execute(source, registry=product.discovery.ops)
    expected = _raw(source, "cedarkit.theta-se", "pte", 500) - _raw(
        source, "cedarkit.theta-se", "pte", 850)
    np.testing.assert_allclose(result.outputs["pte_diff"].values, expected.values)
    assert result.outputs["pte_diff"].attrs == {"units": "K", "temperature_kind": "difference"}
    levels = {request.key.query.extra["first_level"] for request in source.workflow_requests
              if request.key.parameter_id == "cedarkit.theta-se"}
    assert levels == {500.0, 850.0}


def test_qdiv_shearing_and_dewpoint_units():
    source = MockDataSource(resolution=2)
    qdiv = select_workflow_product("cn.qv_div.default")
    output = qdiv.compile(_context({"level": 850})).execute(source, registry=qdiv.discovery.ops).outputs["qdiv"]
    raw = _raw(source, "cedarkit.qdiv", "qv_div", 850)
    expected = smth9(smth9(raw.values, 0.5, -0.25, False), 0.5, -0.25, False) * 1e7
    np.testing.assert_allclose(output.values, expected)
    assert output.attrs["units"] == "10^-7 g/(hPa cm^2 s)"

    shear = select_workflow_product("cn.shr.default")
    shear_source = MockDataSource(resolution=2)
    shear_result = shear.compile(_context({"first_level": 3000, "second_level": 0})).execute(
        shear_source, registry=shear.discovery.ops)
    shear_raw = _raw(shear_source, "cedarkit.shr", "vwsh", 3000, "heightAboveGroundLayer")
    shear_expected = shear_raw.values
    for _ in range(3):
        shear_expected = smth9(shear_expected, 0.5, -0.25, False)
    np.testing.assert_allclose(shear_result.outputs["shr"].values, shear_expected)
    assert shear_result.outputs["shr"].attrs["units"] == "m/s"
    assert shear_source.workflow_requests[0].key.query.extra["first_level"] == 3000
    assert shear_source.workflow_requests[0].key.query.extra["second_level"] == 0

    dew = select_workflow_product("cn.t_dew_t.default")
    dew_source = MockDataSource(resolution=2)
    dew_result = dew.compile(_context({"level": 850})).execute(dew_source, registry=dew.discovery.ops)
    raw_t = _raw(dew_source, "cedarkit.t", "t", 850)
    raw_td = _raw(dew_source, "cedarkit.td", "dpt", 850)
    diff = raw_t.values - raw_td.values
    expected_diff = smth9(smth9(diff, 0.5, 0.25, True), 0.5, 0.25, True)
    expected_t = smth9(smth9(raw_t.values, 0.5, 0.25, True), 0.5, 0.25, True) - 273.15
    np.testing.assert_allclose(dew_result.outputs["depression"].values, expected_diff)
    np.testing.assert_allclose(dew_result.outputs["temperature"].values, expected_t)
    assert dew_result.outputs["depression"].attrs["temperature_kind"] == "difference"
    assert dew_result.outputs["temperature"].attrs["temperature_kind"] == "absolute"
    assert len(dew_source.workflow_requests) == 2


@pytest.mark.parametrize("name,params,unit", (
    ("qv_div", {"level": 850}, "1e-7.g/(cm2.hpa.s)"),
    ("shr", {"first_level": 3000, "second_level": 0}, "s-1"),
))
def test_conflicting_source_units_fail_explicitly(name, params, unit):
    product = select_workflow_product(f"cn.{name}.default")

    class ConflictingSource(MockDataSource):
        def fetch_many(self, requests):
            fields = super().fetch_many(requests)
            for field in fields:
                field.attrs["units"] = unit
            return fields

    with pytest.raises(PlanExecutionError, match="source_units|unknown unit"):
        product.compile(_context(params)).execute(ConflictingSource(resolution=2),
                                                   registry=product.discovery.ops)
