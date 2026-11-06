"""Public reki sources preserve raw values and identity through cn.t2m."""

from dataclasses import asdict, replace
import json

import eccodes
import numpy as np
import pytest
import reki
import xarray as xr
from cedarkit_query import Query, QueryError, SourceError

from cedar_graph.data import RekiProvider
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedarkit.plots.workflow.plan import CompileContext, BoundFieldRequest, public_request_from_field_request
from reki.diagnostics import collect_io_metrics


def _fixture(tmp_path):
    path = tmp_path / "arbitrary-name.grib2"
    message = eccodes.codes_grib_new_from_samples("regular_ll_sfc_grib2")
    try:
        for key, value in {
            "centre": 38, "subCentre": 0, "tablesVersion": 4, "localTablesVersion": 0,
            "productionStatusOfProcessedData": 0, "discipline": 0,
            "parameterCategory": 0, "parameterNumber": 0,
            "dataDate": 20260830, "dataTime": 0, "significanceOfReferenceTime": 1,
            "forecastTime": 24, "typeOfLevel": "heightAboveGround", "level": 2,
            "Ni": 4, "Nj": 3, "latitudeOfFirstGridPointInDegrees": 50,
            "latitudeOfLastGridPointInDegrees": 48, "longitudeOfFirstGridPointInDegrees": 100,
            "longitudeOfLastGridPointInDegrees": 103, "iDirectionIncrementInDegrees": 1,
            "jDirectionIncrementInDegrees": 1,
        }.items():
            eccodes.codes_set(message, key, value)
        eccodes.codes_set_values(message, np.arange(280., 292.))
        path.write_bytes(eccodes.codes_get_message(message))
    finally:
        eccodes.codes_release(message)
    # The file location needs no catalog registration. Dataset declares which
    # parameter definitions interpret named business variables in its contents.
    source = {"kind": "file", "path": str(path), "dataset": "cma_gfs_gmf"}
    product = select_workflow_product("cn.t2m")
    workflow = product.compile(CompileContext(
        start_time="2026-08-30T00:00:00Z", forecast_time="24h",
        params={"style_variant": "cn_summer", "model": "CMA-GFS"}))
    node = next(item for item in workflow.nodes if item.request is not None)
    request = BoundFieldRequest(node.id, node.request, node.origin)
    return source, workflow, request, product


def test_product_matches_public_reki_dataset_and_preserves_identity(tmp_path):
    source, workflow, request, product = _fixture(tmp_path)
    public = public_request_from_field_request(request, source=source)
    with reki.from_source(source) as owner:
        field = owner.sel(public.queries).one()
        direct = field.to_xarray()
        expected_reference = json.loads(json.dumps(dict(field.metadata["source"])))
    with RekiProvider(source) as provider:
        assert workflow.check_available(provider).requests[0].status == "available"
        raw = provider.fetch(request)
        assert raw.dims == ("latitude", "longitude")
        assert raw.time.values == np.datetime64("2026-08-30T00:00:00", "ns")
        assert raw.valid_time.values == np.datetime64("2026-08-31T00:00:00", "ns")
        assert raw.step.values == np.timedelta64(24, "h")
        assert raw.height_above_ground.item() == 2
        assert raw.attrs["units"] == "K"
        assert json.loads(raw.attrs["source_reference"]) == expected_reference
        np.testing.assert_array_equal(raw.values, direct.t2m.values[0, 0, 0])
        np.testing.assert_array_equal(raw.values, np.arange(280., 292.).reshape(3, 4))
        result = workflow.execute(provider, registry=product.discovery.ops)
        converted = result.outputs["temperature"]
        np.testing.assert_allclose(converted.values, raw.values - 273.15)
        assert converted.attrs["units"] == "degC"
        assert converted.valid_time.identical(raw.valid_time)
        assert provider.query_reports[0]["overall"]["field_count"] == 1
        assert provider.trace[0].field_identity["parameter"] == "cedarkit.t2m"
        assert provider.trace[0].source_reference == expected_reference
        json.dumps([asdict(trace) for trace in provider.trace])
    assert provider.trace and provider.query_reports
    assert provider.cache_info["entries"] == 0
    with pytest.raises(RuntimeError, match="closed"):
        provider.fetch(request)
    # Returned arrays remain usable after closing their owner.
    np.testing.assert_array_equal(raw.values, np.arange(280., 292.).reshape(3, 4))


def test_preflight_decodes_no_values_and_cache_is_mutation_safe(tmp_path):
    source, _, request, _ = _fixture(tmp_path)
    with RekiProvider(source) as provider:
        with collect_io_metrics() as metrics:
            assert provider.check_many((request, request)) == ["available", "available"]
        assert metrics.snapshot()["value_decode_count"] == 0
        with collect_io_metrics() as cold:
            values = provider.fetch_many((request, request))
        assert cold.snapshot()["value_decode_count"] == 1
        values[0].values[:] = 999
        with collect_io_metrics() as hot:
            again = provider.fetch(request)
        assert hot.snapshot()["value_decode_count"] == 0
        assert hot.snapshot()["grib_header_scan_count"] == 0
        np.testing.assert_array_equal(again.values, values[1].values)
        assert [trace.status for trace in provider.trace] == ["ok", "cached", "cached"]
        assert provider.trace[1].query_report == provider.trace[0].query_report


def test_missing_file_is_structured_and_never_a_decoded_empty_result(tmp_path):
    source, workflow, request, _ = _fixture(tmp_path)
    with RekiProvider(source) as provider:
        (tmp_path / "arbitrary-name.grib2").unlink()
        assert workflow.check_available(provider).requests[0].status == "missing"
        with pytest.raises(SourceError) as caught:
            provider.fetch(request)
        assert caught.value.code == "resource_not_found"
        assert provider.trace[-1].status == "error"
        assert provider.trace[-1].error_code == "resource_not_found"


def test_absent_field_keeps_cardinality_and_optional_lookup_semantics(tmp_path):
    source, _, request, _ = _fixture(tmp_path)
    query = Query({"parameter": "cedarkit.t", "level_type": "pressure", "level": 850})
    missing = replace(request, key=replace(request.key, query=query, parameter_id="cedarkit.t"))
    with RekiProvider(source) as provider:
        assert provider.check_many((missing,)) == ["missing"]
        with pytest.raises(QueryError) as caught:
            provider.fetch(missing)
        assert caught.value.code == "no_match"
        optional = replace(missing, key=replace(missing.key, cardinality="all"))
        assert provider.fetch(optional) is None
        assert provider.trace[-1].query_report["overall"]["field_count"] == 0


def test_plot_adapter_preserves_single_point_spatial_grid_and_rejects_many_times():
    dataset = xr.Dataset({"t2m": (("time", "latitude", "longitude"), [[[280.]]])},
                         coords={"time": [np.datetime64("2026-08-30")],
                                 "latitude": [30.], "longitude": [110.]})
    kwargs = dict(parameter_id="cedarkit.t2m", report={}, identity={}, reference={})
    field = RekiProvider._plot_array(dataset, **kwargs)
    assert field.dims == ("latitude", "longitude")
    assert field.shape == (1, 1)
    assert field.time.ndim == 0
    many = xr.concat([dataset, dataset.assign_coords(time=[np.datetime64("2026-08-31")])], dim="time")
    with pytest.raises(QueryError) as caught:
        RekiProvider._plot_array(many, **kwargs)
    assert caught.value.code == "multiple_matches"
