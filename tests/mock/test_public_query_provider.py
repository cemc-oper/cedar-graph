"""T15: the existing cn.t2m product shares one public field with reki and CLI."""

import json

import eccodes
import numpy as np
import xarray as xr
from click.testing import CliRunner

from cedar_graph.data import RekiProvider
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedarkit.plots.workflow.plan import CompileContext, BoundFieldRequest, public_request_from_field_request
from cedarkit.plots.workflow.plan.model import FieldRequest
from reki.catalog import load_catalog
from reki.catalog.query_binding import CatalogSnapshot, builtin_catalog_snapshot, plan_source_binding
from reki.cli import cli
from reki.diagnostics import collect_io_metrics
from reki.parameter_adapter import FROZEN_REGISTRY_SHA256
from reki.query_collection import read_grib_collection
from reki.readers.grib.config import resolve_parameter


def _fixture(tmp_path):
    path = tmp_path / "t2m.grib2"
    message = eccodes.codes_grib_new_from_samples("regular_ll_pl_grib2")
    try:
        for key, value in (
            ("shortName", "2t"), ("dataDate", 20260830), ("dataTime", 0),
            ("forecastTime", 24), ("typeOfLevel", "heightAboveGround"), ("level", 2),
            ("Ni", 4), ("Nj", 3), ("latitudeOfFirstGridPointInDegrees", 50),
            ("latitudeOfLastGridPointInDegrees", 48), ("longitudeOfFirstGridPointInDegrees", 100),
            ("longitudeOfLastGridPointInDegrees", 103), ("iDirectionIncrementInDegrees", 1),
            ("jDirectionIncrementInDegrees", 1),
        ):
            eccodes.codes_set(message, key, value)
        eccodes.codes_set_values(message, [280.0 + index for index in range(12)])
        path.write_bytes(eccodes.codes_get_message(message))
    finally:
        eccodes.codes_release(message)
    catalog = {"api_version": "reki.catalog/v1", "datasets": [{"id": "grid", "source": {
        "name": "file-pattern", "args": [str(tmp_path), "t2m.grib2"]}}]}
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(catalog))
    snapshot = CatalogSnapshot(load_catalog(builtin=False, plugins=False, user=False,
                                           explicit=catalog), "t15-catalog")
    workflow = select_workflow_product("cn.t2m").compile(CompileContext(
        start_time="2026-08-30T00:00:00Z", forecast_time="24h",
        params={"style_variant": "cn_summer"}))
    node = next(item for item in workflow.nodes if item.request is not None)
    request = BoundFieldRequest(node.id, node.request, node.origin)
    return path, catalog_path, snapshot, workflow, request


def _provider(snapshot, path):
    return RekiProvider.from_query_catalog(snapshot, "grid",
                                           native_parameters={"cedarkit.t2m": "2t"},
                                           candidate_paths=[path], index_policy="off")


def _cli(catalog_path, action, request):
    return CliRunner().invoke(cli, ["request", "--catalog", str(catalog_path),
                                    "--catalog-version", "t15-catalog", "--native-parameter",
                                    "cedarkit.t2m=2t", action, "--input-format", "json"],
                              input=json.dumps(request))


def test_product_public_query_matches_direct_cli_and_provider(tmp_path):
    path, catalog_path, snapshot, workflow, request = _fixture(tmp_path)
    public = public_request_from_field_request(request, dataset="grid", native_parameter="2t")
    binding = plan_source_binding(public.query, snapshot=snapshot)
    direct = read_grib_collection(binding, candidate_paths=[path],
                                  native_parameters={"cedarkit.t2m": "2t"}, index_policy="off")
    expected_reference = direct.fields[0].reference.to_dict()

    located_request = public.to_dict()
    located_request["action"] = "locate"
    located = _cli(catalog_path, "locate", located_request)
    assert located.exit_code == 0, located.output
    assert json.loads(located.output)["references"] == [expected_reference]

    output = tmp_path / "t2m.nc"
    read_request = public.to_dict()
    read_request["options"] = {"output": {"format": "netcdf", "path": str(output)}}
    read = _cli(catalog_path, "read", read_request)
    assert read.exit_code == 0, read.output
    assert json.loads(read.output)["references"] == [expected_reference]
    with xr.open_dataarray(output, engine="scipy") as cli_data:
        assert cli_data.coords["heightAboveGroundInM"].values.tolist() == [2]
        np.testing.assert_array_equal(cli_data.isel(lead_time=0, heightAboveGroundInM=0).values,
                                      direct.fields[0].data.values)
        assert cli_data.attrs["units"] == "K"

    with _provider(snapshot, path) as provider:
        assert workflow.check_available(provider).requests[0].status == "available"
        native = provider.fetch(request)
        assert native.attrs["source_reference"] == expected_reference
        assert native.attrs["units"] == "K"
        np.testing.assert_array_equal(native.values, direct.fields[0].data.values)
        result = workflow.execute(provider, registry=select_workflow_product("cn.t2m").discovery.ops)
        np.testing.assert_allclose(result.outputs["temperature"].values, native.values - 273.15)
        assert result.outputs["temperature"].attrs["units"] == "degC"
        assert request.node_id.startswith("read:")
        assert "node_id" not in public.to_dict()["query"]


def test_batch_reuses_native_field_and_preflight_only_reads_headers(tmp_path):
    path, _, snapshot, workflow, request = _fixture(tmp_path)
    with _provider(snapshot, path) as provider:
        with collect_io_metrics() as metrics:
            assert provider.check_many((request, request)) == ["available", "available"]
        assert metrics.snapshot()["value_decode_count"] == 0
        with collect_io_metrics() as cold:
            values = provider.fetch_many((request, request))
        assert len(values) == 2
        assert cold.snapshot()["value_decode_count"] == 1
        assert provider.cache_info["hits"] >= 1
        values[0].values[:] = 999
        with collect_io_metrics() as hot:
            again = provider.fetch(request)
        assert hot.snapshot()["value_decode_count"] == 0
        assert hot.snapshot()["grib_header_scan_count"] == 0
        np.testing.assert_array_equal(again.values, values[1].values)
        assert [trace.status for trace in provider.trace] == ["ok", "ok", "ok"]


def test_missing_candidate_is_reported_before_workflow_execution(tmp_path):
    path, _, snapshot, workflow, request = _fixture(tmp_path)
    path.unlink()
    with _provider(snapshot, path) as provider:
        report = workflow.check_available(provider)
        assert report.requests[0].status == "missing"
        assert not report.executable


def test_preflight_uses_the_same_explicit_candidates_as_read(tmp_path):
    path, _, snapshot, _, request = _fixture(tmp_path)
    with _provider(snapshot, tmp_path / "missing.grib2") as provider:
        assert provider.check_many((request,)) == ["missing"]
    alternative = tmp_path / "alternative.grib2"
    path.rename(alternative)
    with _provider(snapshot, alternative) as provider:
        assert provider.check_many((request,)) == ["available"]
        assert provider.fetch(request).attrs["source_reference"]["resource"]["locator"] == str(alternative)


def test_remote_preflight_is_unknown_only_for_frozen_supported_field(monkeypatch, tmp_path):
    from reki.sources import cmadaas as source_module

    monkeypatch.setattr(source_module, "_import_module", lambda name: (_ for _ in ()).throw(
        AssertionError("preflight imported CMADaaS client")))
    snapshot = builtin_catalog_snapshot()
    field = FieldRequest("default", "cedarkit.t", resolve_parameter(
        "cedarkit.t", level_type="surface", step_type="instant",
        extra={"typeOfFirstFixedSurface": 1}).query,
        "2026-08-30T00:00:00Z", "P1DT0H0M0S", "one")
    request = BoundFieldRequest("read:frozen", field, "test")
    with RekiProvider.from_query_catalog(snapshot, "cma_gfs_gmf_cmadaas",
                                         native_parameters={"cedarkit.t": "t"},
                                         registry_sha256=FROZEN_REGISTRY_SHA256) as provider:
        with collect_io_metrics() as metrics:
            assert provider.check_many((request,)) == ["unknown"]
        assert metrics.snapshot()["file_open_count"] == 0

    _, _, _, _, t2m_request = _fixture(tmp_path)
    with RekiProvider.from_query_catalog(snapshot, "cma_gfs_gmf_cmadaas",
                                         native_parameters={"cedarkit.t2m": "2t"},
                                         registry_sha256=FROZEN_REGISTRY_SHA256) as provider:
        assert provider.check_many((t2m_request,)) == ["invalid"]
