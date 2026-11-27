"""Real member/control/MAX content is owned by the ensemble caller."""

import numpy as np
import pytest

from cedarkit.plots.config import BasemapSpec, Cell, MapFeatureSpec
from cedarkit.plots.map import MapLoader, MapType
from cedarkit.plots.templates import ens_cn
from cedar_graph.recipes.ensemble_product import EnsembleRequest, EnsembleT2MProduct
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.runtime import PlanExecutionError


class EmptyLoader(MapLoader):
    def get_feature(self, name: str, **kwargs):
        return []


def _basemap():
    return BasemapSpec(loader=EmptyLoader, map_type=MapType.Portrait, features=())


def _prepare(request, provider=None):
    provider = provider or MockDataSource(resolution=5)
    result = EnsembleT2MProduct().prepare(provider, start_time="2024-07-01",
                                          forecast_time="24h", request=request)
    return result, provider


@pytest.mark.parametrize("member_count", (1, 4, 14))
def test_member_count_max_identity_and_shared_colorbar(member_count):
    member_ids = tuple(f"m{number:02d}" for number in range(1, member_count + 1))
    prepared, provider = _prepare(EnsembleRequest(member_ids, control_id="ctl"))
    assert prepared.realized_member_ids == member_ids
    assert prepared.realized_control_id == "ctl"
    assert prepared.max_input_ids == member_ids
    assert prepared.provider_requests == len(provider.workflow_requests) == member_count + 1
    queries = [request.key.query.to_dict() for request in provider.workflow_requests]
    assert {query["member"] for query in queries if "member" in query} == set(range(1, member_count + 1))
    assert sum(query.get("member_role") == "control" for query in queries) == 1
    np.testing.assert_allclose(prepared.max_field.values,
                               np.maximum.reduce([prepared.fields[member].values for member in member_ids]))
    panel = prepared.render(basemap=_basemap())
    try:
        assert len(panel.charts) == member_count + 2
        assert panel.charts["ctl"].role == "control"
        assert panel.charts["max"].role == "max"
        assert all(panel.charts[member].role == "member" for member in member_ids)
        assert "ens_cn_colorbar" in panel.effective_config.decorations.colorbars
        assert len(panel.fig.axes) == len(panel.charts) + 1
        assert max(chart.main.ax.bbox.x1 for chart in panel.charts.values()) < panel.fig.axes[-1].bbox.x0
        boundaries = [chart.layers["temperature"].results["main"].mappable.norm.boundaries
                      for chart in panel.charts.values()]
        for levels in boundaries[1:]:
            np.testing.assert_array_equal(levels, boundaries[0])
    finally:
        panel.close()


def test_five_to_three_column_reflow_keeps_chart_and_layer_identity_without_fetching():
    members = tuple(f"m{number:02d}" for number in range(1, 15))
    prepared, provider = _prepare(EnsembleRequest(members, control_id="ctl"))
    panel = prepared.render(basemap=_basemap(), empty_slots={"reserved": Cell(row=0, column=4)})
    try:
        assert panel.effective_config.layout.columns == 5
        assert panel.effective_config.layout.rows == 4
        assert panel.effective_config.layout.slots["reserved"].kind == "empty"
        charts = tuple(panel.charts.values())
        layers = tuple(panel.charts[chart.id].layers["temperature"] for chart in charts)
        first_figure = panel.fig
        panel.apply_template(ens_cn(columns=3, control_id="ctl", max_id="max",
                                    basemap=_basemap(), empty_slots={"reserved": Cell(row=0, column=2)}))
        assert panel.effective_config.layout.columns == 3
        assert panel.effective_config.layout.rows == 6
        assert tuple(panel.charts.values()) == charts
        assert tuple(panel.charts[chart.id].layers["temperature"] for chart in charts) == layers
        panel.render()
        assert panel.fig is not first_figure
        assert len(provider.workflow_requests) == 15
    finally:
        panel.close()


def test_control_is_optional_and_max_can_include_it_explicitly():
    class HighControl(MockDataSource):
        def fetch_many(self, requests):
            fields = super().fetch_many(requests)
            for index, (request, field) in enumerate(zip(requests, fields)):
                if request.key.query.to_dict().get("member_role") == "control":
                    attrs = dict(field.attrs)
                    fields[index] = field + 20
                    fields[index].attrs = attrs
            return fields

    source = HighControl(resolution=5)
    without, _ = _prepare(EnsembleRequest(("m01", "m02"), control_id="ctl"), source)
    with_control, _ = _prepare(EnsembleRequest(("m01", "m02"), control_id="ctl",
                                                include_control_in_max=True), source)
    assert without.max_input_ids == ("m01", "m02")
    assert with_control.max_input_ids == ("m01", "m02", "ctl")
    assert float(with_control.max_field.mean()) > float(without.max_field.mean())
    no_control, _ = _prepare(EnsembleRequest(("m01", "m02"), max_enabled=False))
    assert no_control.realized_control_id is None and no_control.max_field is None
    panel = no_control.render(basemap=_basemap())
    try:
        assert tuple(panel.charts) == ("m01", "m02")
        assert panel.validate(complete=True) == ()
    finally:
        panel.close()


@pytest.mark.parametrize("coordinate", ("number", "member"))
def test_grib_member_number_is_preserved_on_members_and_ignored_for_max_grid(coordinate):
    class NumberedSource(MockDataSource):
        def fetch_many(self, requests):
            fields = super().fetch_many(requests)
            numbered = []
            for request, field in zip(requests, fields):
                field = field.assign_coords({coordinate: request.key.query.member})
                field.attrs.pop("standard_name", None)
                numbered.append(field)
            return numbered

    request = EnsembleRequest(("m001", "m002"), control_id="m000",
                              include_control_in_max=True)
    prepared, _ = _prepare(request, NumberedSource(resolution=5))
    assert [prepared.fields[member].coords[coordinate].item()
            for member in ("m000", "m001", "m002")] == [0, 1, 2]
    assert coordinate not in prepared.max_field.coords
    assert all(field.attrs["standard_name"] == "air_temperature"
               for field in (*prepared.fields.values(), prepared.max_field))
    np.testing.assert_allclose(prepared.max_field.values,
                               np.maximum.reduce([prepared.fields[member].values
                                                  for member in prepared.max_input_ids]))
    panel = prepared.render(basemap=_basemap())
    try:
        assert "ens_cn_colorbar" in panel.effective_config.decorations.colorbars
    finally:
        panel.close()


def test_missing_members_are_recorded_or_rejected_by_policy():
    class MissingSource(MockDataSource):
        def fetch_many(self, requests):
            values = super().fetch_many(requests)
            return [None if request.key.query.to_dict().get("member") == 2 else value
                    for request, value in zip(requests, values)]

    request = EnsembleRequest(("m01", "m02", "m03"), control_id="ctl", missing_policy="skip")
    prepared, source = _prepare(request, MissingSource(resolution=5))
    assert prepared.realized_member_ids == ("m01", "m03")
    assert prepared.missing_member_ids == ("m02",)
    assert prepared.max_input_ids == ("m01", "m03")
    assert len(source.workflow_requests) == 4
    with pytest.raises(PlanExecutionError, match="m02"):
        _prepare(EnsembleRequest(("m01", "m02"), missing_policy="error"), MissingSource(resolution=5))
    with pytest.raises(ValueError, match="no available members"):
        _prepare(EnsembleRequest(("m02",), missing_policy="skip"), MissingSource(resolution=5))


def test_invalid_ids_and_control_policy_fail_before_fetching():
    with pytest.raises(ValueError, match="list or tuple"):
        EnsembleRequest("m01")
    with pytest.raises(ValueError, match="unique"):
        EnsembleRequest(("m01", "m01"))
    with pytest.raises(ValueError, match="distinct"):
        EnsembleRequest(("m01",), control_id="m01")
    with pytest.raises(ValueError, match="requires control_id"):
        EnsembleRequest(("m01",), include_control_in_max=True)


@pytest.mark.parametrize("members,control", [(("m1", "m001"), None), (("m000",), "ctl")])
def test_member_aliases_cannot_count_one_native_member_twice(members, control):
    with pytest.raises(ValueError, match="unique|distinct"):
        EnsembleRequest(members, control_id=control)


def test_max_tracks_per_point_valid_inputs_and_drops_single_member_identity():
    import json
    import pandas as pd
    class MaskedSource(MockDataSource):
        def fetch_many(self, requests):
            fields = super().fetch_many(requests)
            for request, field in zip(requests, fields):
                field.values[0, 0] = np.nan
                if request.key.query.member == 1:
                    field.values[0, 1] = np.nan
                origin = pd.Timestamp(request.key.start_time)
                origin = origin.tz_localize("UTC") if origin.tzinfo is None else origin
                identity = {"parameter": "cedarkit.t2m", "member": request.key.query.member,
                    "member_role": "perturbation", "time": origin.isoformat(),
                    "valid_time": (origin + pd.Timedelta(request.key.forecast_time)).isoformat(),
                    "level_type": "height_above_ground", "level": 2}
                field.attrs.update(field_identity=json.dumps(identity),
                    source_reference=json.dumps({"sample": 1}),
                    cedarkit_query_report=json.dumps({"overall": {"status": "unchecked"}}))
            return fields
    prepared, _ = _prepare(EnsembleRequest(("m01", "m02")), MaskedSource(resolution=5))
    assert np.isnan(prepared.max_field.values[0, 0])
    assert prepared.max_valid_count.values[0, 0] == 0
    assert prepared.max_valid_count.values[0, 1] == 1
    assert "cedarkit_query_report" not in prepared.max_field.attrs
    assert "source_reference" not in prepared.max_field.attrs
    assert "field_identity" not in prepared.max_field.attrs
    assert len(json.loads(prepared.max_field.attrs["source_field_identities"])) == 2
    assert prepared.summary()["max_requested_input_count"] == 2
    assert prepared.summary()["max_realized_input_count"] == 2
    assert prepared.summary()["valid_input_count_min"] == 0


@pytest.mark.parametrize("case", ["identity", "grid", "infinity"])
def test_invalid_member_inputs_fail_before_aggregation(case):
    import json
    class InvalidSource(MockDataSource):
        def fetch_many(self, requests):
            fields = super().fetch_many(requests)
            if case == "identity":
                fields[0].attrs["field_identity"] = json.dumps({"parameter": "wrong"})
            elif case == "grid" and requests[-1].key.query.member == 2:
                fields[-1] = fields[-1].assign_coords(longitude=fields[-1].longitude + 1)
            else:
                fields[-1].values[0, 0] = np.inf
            return fields
    with pytest.raises(ValueError, match="identity|grids|infinite"):
        _prepare(EnsembleRequest(("m01", "m02")), InvalidSource(resolution=5))
