"""The wind product keeps physical arrays separate from barb encoding."""

import numpy as np
import pytest
import xarray as xr

from cedar_graph.recipes.workflow_product import select_workflow_product
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.plan import CompileContext
from cedarkit.plots.workflow.runtime import PlanExecutionError


class KnownWindSource:
    def __init__(self):
        coords = {
            "latitude": [45.0, 35.0, 25.0], "longitude": [90.0, 110.0, 130.0],
            "time": np.datetime64("2026-11-02T12:00:00"),
            "step": np.timedelta64(6, "h"),
            "valid_time": np.datetime64("2026-11-02T18:00:00"),
            "height_above_ground": 10.0,
        }
        self.fields = {
            "cedarkit.u10m": xr.DataArray(
                [[0.0, 10.0, -20.0], [3.0, np.nan, 8.0], [0.0, -3.0, 6.0]],
                dims=("latitude", "longitude"), coords=coords, attrs={"units": "m/s"}),
            "cedarkit.v10m": xr.DataArray(
                [[0.0, 0.0, 0.0], [4.0, 6.0, np.nan], [-10.0, -4.0, 8.0]],
                dims=("latitude", "longitude"), coords=coords, attrs={"units": "m/s"}),
        }
        self.requests = []

    def fetch_many(self, requests):
        self.requests.extend(requests)
        return [self.fields[request.key.parameter_id] for request in requests]


def wind_plan():
    product = select_workflow_product("cn.wind_10m")
    return product, product.compile(CompileContext(
        start_time="2026-11-02T12:00:00Z", forecast_time="6h",
        params={"model": "CMA-GFS"}))


def test_physical_components_speed_directions_and_masks_remain_in_mps():
    product, plan = wind_plan()
    source = KnownWindSource()
    original = {name: field.copy(deep=True) for name, field in source.fields.items()}
    result = plan.execute(source, registry=product.discovery.ops)

    for name, parameter in (("u_10m", "cedarkit.u10m"), ("v_10m", "cedarkit.v10m")):
        xr.testing.assert_identical(result.outputs[name], original[parameter])
        xr.testing.assert_identical(source.fields[parameter], original[parameter])
    speed = result.outputs["ws_10m"]
    np.testing.assert_array_equal(speed.values, [
        [0.0, 10.0, 20.0], [5.0, np.nan, np.nan], [10.0, 5.0, 10.0]])
    assert speed.attrs["units"] == "m/s"
    assert speed.coords.equals(original["cedarkit.u10m"].coords)
    assert len(source.requests) == plan.read_count == 2
    assert {request.key.query.parameter for request in source.requests} == {"cedarkit.u10m", "cedarkit.v10m"}
    assert all(request.key.query.level_type == "height_above_ground"
               and request.key.query.level == 10 for request in source.requests)


def test_conflicting_component_units_are_rejected_before_wind_speed():
    product, plan = wind_plan()
    source = KnownWindSource()
    source.fields["cedarkit.v10m"].attrs["units"] = "knots"
    with pytest.raises(PlanExecutionError, match="source_units.*contradicts") as caught:
        plan.execute(source, registry=product.discovery.ops)
    assert isinstance(caught.value.cause, ValueError)


def test_wind_render_uses_physical_encoding_and_forecast_identity():
    product, plan = wind_plan()
    assert plan.content.charts[0].titles[0].text == (
        "10m Wind and Wind Speed (m/s)\n"
        "CMA-GFS | Init 2026110212 UTC | Valid 2026110218 UTC | +006h\n"
        "Barbs: half 2 / full 4 / flag 20 m/s")
    assert plan.content.colorbars[0].label == "m/s"
    panel = product.run(MockDataSource(resolution=5), CompileContext(
        start_time="2026-11-02T12:00:00Z", forecast_time="6h"))
    try:
        main = panel.charts["main"]
        assert tuple(main.layers["ws_10m_0"].results) == ("main", "south_china_sea")
        assert tuple(main.layers["wind_1"].results) == ("main",)
        assert main.layers["wind_1"].style.barb_increments == {"half": 2, "full": 4, "flag": 20}
        assert main.layers["wind_1"].style.expected_units == "m/s"
    finally:
        panel.close()


def test_mock_surface_wind_accepts_the_public_height_coordinate():
    source = MockDataSource(resolution=5)
    for parameter in ("cedarkit.u10m", "cedarkit.v10m"):
        current = source.field(parameter, level_type="height_above_ground", level=10)
        legacy = source.field(parameter, level_type="heightAboveGround", level=10)
        xr.testing.assert_identical(current, legacy)
