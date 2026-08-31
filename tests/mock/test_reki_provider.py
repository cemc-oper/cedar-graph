import pandas as pd
import pytest
import xarray as xr
import numpy as np
from pathlib import Path

import reki
from cedar_graph.data import DataLoader, RekiProvider
from cedar_graph.data.field_info import t_2m_info
from cedar_graph.recipes.engine import RECIPE_FIELDS, get_recipe_engine
from cedarkit.plots.ops import OpRegistry
from cedar_graph.plots.cn.t_dew_t.default import load_data as load_t_dew_t
from cedarkit.plots.plan import CompileContext, compile_recipe
from cedarkit.plots.plan.nodes import RequestKey, TimeBinding
from cedarkit.plots.plan.provider import BoundFieldRequest
from cedarkit.plots.recipe import load_recipe


class _Field:
    def __init__(self, data):
        self.data = data

    def to_xarray(self):
        return self.data


class _Reader:
    def __init__(self, data):
        self.data = data
        self.query = None

    def sel(self, query):
        self.query = query
        return self

    def one(self):
        return _Field(self.data)

    def one_or_none(self):
        return None


class _BatchReader(_Reader):
    class _Capabilities:
        fetch_many = True

    capabilities = _Capabilities()

    def fetch_many(self, queries, *, cardinality):
        assert cardinality == "one"
        return [_Field(self.data) for _ in queries]


class _DirectReader:
    def __init__(self, data):
        self.data = data
        self.sel_calls = 0

    def sel(self, query):
        self.sel_calls += 1
        raise AssertionError("CMADaaS direct-result fields must not be selected")

    def to_xarray(self):
        return self.data


def _recipe_fixture(parameter, forecast_time):
    """Small fixed field set shared by the selectable and MUSIC mocks."""
    values = {
        0: 273.15,  # temperature
        2: 4.0,     # u wind
        3: -2.0,    # v wind
        8: pd.Timedelta(forecast_time).total_seconds() / 3600.0 + 3.0,
    }
    value = values[parameter]
    return xr.DataArray(
        [[value, float("nan")], [value + 1.0, value + 2.0]],
        dims=("latitude", "longitude"),
        coords={"latitude": [30.0, 31.0], "longitude": [110.0, 111.0]},
        attrs={"units": "K" if parameter == 0 else "mm" if parameter == 8 else "m/s"},
    )


class _RecipeLocalReader:
    """Deterministic local-GRIB-shaped reader retaining ``sel`` semantics."""
    class _Capabilities:
        fetch_many = True

    capabilities = _Capabilities()

    def __init__(self, forecast_time):
        self.query = None
        self.forecast_time = forecast_time

    def sel(self, query):
        self.query = query
        return self

    def one(self):
        return _Field(_recipe_fixture(query_parameter_number(self.query), self.forecast_time))

    def fetch_many(self, queries, *, cardinality):
        assert cardinality == "one"
        return [_Field(_recipe_fixture(query_parameter_number(query), self.forecast_time))
                for query in queries]


def query_parameter_number(query):
    return query.parameter["parameterNumber"]


def _request(parameter_id="cedarkit.t2m", *, node_id="read.t2m"):
    return BoundFieldRequest(
        node_id=node_id,
        key=RequestKey(
            provider_slot="default", parameter_id=parameter_id,
            query=reki.resolve_parameter(parameter_id).query,
            time_binding=TimeBinding(pd.Timestamp("2026-01-01"), pd.Timedelta(hours=6)),
        ),
        origin="test",
    )


def test_provider_binds_times_and_uses_strict_api(monkeypatch):
    reader = _Reader(xr.DataArray([1], attrs={"units": "K"}))
    calls = []
    monkeypatch.setattr(reki, "from_source", lambda spec, **kwargs: calls.append((spec, kwargs)) or reader)
    provider = RekiProvider(reki.SourceSpec("local", args=("archive",)))
    result = provider.load(reki.FieldQuery(parameter="2t"), start_time=pd.Timestamp("2026-01-01"), forecast_time="6h")
    assert result.identical(reader.data)
    assert reader.query == reki.FieldQuery(parameter="2t")
    assert calls[0][1]["forecast_time"] == "6h"


def test_provider_batch_prototype_does_not_change_recipe_load(monkeypatch):
    reader = _BatchReader(xr.DataArray([1]))
    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: reader)
    provider = RekiProvider(reki.SourceSpec("local"))
    result = provider._load_many([reki.FieldQuery(parameter="t"), reki.FieldQuery(parameter="u")])
    assert len(result) == 2


def test_cmadaas_provider_binds_direct_result_without_sel(monkeypatch):
    catalog = reki.load_catalog(plugins=False, user=False)
    dataset = catalog.resolve("CMA-GFS-CMADaaS")
    reader = _DirectReader(xr.DataArray([[273.15]], dims=("latitude", "longitude"), attrs={"units": "K"}))
    calls = []
    monkeypatch.setattr(reki, "from_source", lambda spec, **kwargs: calls.append((spec, kwargs)) or reader)
    provider = RekiProvider(dataset)

    result = provider.fetch(_request())

    assert result.name == "cedarkit.t2m"
    assert result.attrs["cmadaas_parameter"] == "TEM"
    assert reader.sel_calls == 0
    assert calls == [(dataset.source, {
        "parameter": "TEM", "level_type": 103, "level": 2,
        "start_time": pd.Timestamp("2026-01-01"), "forecast_time": pd.Timedelta(hours=6),
    })]
    assert provider.trace[-1].dataset_id == "cma_gfs_gmf_cmadaas"
    assert provider.trace[-1].catalog_origin == "builtin"
    assert provider.trace[-1].external_parameter == "TEM"


def test_cmadaas_provider_keeps_runtime_region_out_of_plan_identity(monkeypatch):
    catalog = reki.load_catalog(plugins=False, user=False)
    reader = _DirectReader(xr.DataArray([[273.15]], attrs={"units": "K"}))
    calls = []
    monkeypatch.setattr(reki, "from_source", lambda spec, **kwargs: calls.append(kwargs) or reader)
    provider = RekiProvider(catalog.resolve("CMA-GFS-CMADaaS"), region={"type": "rect", "min_latitude": 39})

    provider.fetch(_request())

    assert calls[0]["region"] == {"type": "rect", "min_latitude": 39}


def test_cmadaas_batch_fallback_and_availability_are_ordered_and_unknown(monkeypatch):
    catalog = reki.load_catalog(plugins=False, user=False)
    reader = _DirectReader(xr.DataArray([[273.15]], attrs={"units": "K"}))
    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: reader)
    provider = RekiProvider(catalog.resolve("CMA-GFS-CMADaaS"))
    requests = (_request(node_id="first"), _request(node_id="second"))

    values = provider.fetch_many(requests)

    assert [value.name for value in values] == ["cedarkit.t2m", "cedarkit.t2m"]
    assert [item.node_id for item in provider.trace] == ["first", "second"]
    assert provider.check_many(requests) == ["unknown", "unknown"]


def test_loader_provider_adapts_legacy_field_info(monkeypatch):
    provider = RekiProvider(reki.SourceSpec("local"))
    captured = {}
    monkeypatch.setattr(provider, "load", lambda query, **kwargs: captured.update(query=query, **kwargs) or None)
    loader = DataLoader(provider=provider)
    assert loader.load(t_2m_info, pd.Timestamp("2026-01-01"), pd.Timedelta(hours=3)) is None
    assert captured["query"] == t_2m_info.to_field_query()
    assert captured["required"] is True


def test_loader_requires_one_backend():
    with pytest.raises(TypeError):
        DataLoader()


def test_t2m_recipe_loads_through_provider(monkeypatch):
    """The stage-1 recipe pilot goes through FieldInfo -> FieldQuery."""
    reader = _Reader(xr.DataArray([[273.15]], dims=("latitude", "longitude"), attrs={"units": "K"}))
    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: reader)
    provider = RekiProvider(reki.SourceSpec("local", args=("fixture",)))
    engine = get_recipe_engine()
    recipe_path = Path(__file__).parents[2] / "cedar_graph" / "recipes" / "cn" / "t2m.yaml"
    module = engine.build_module(engine.load_recipe(recipe_path))
    result = module.load_data(
        data_loader=DataLoader(provider=provider),
        start_time=pd.Timestamp("2026-01-01"), forecast_time=pd.Timedelta(hours=6),
    )
    assert result.t2m.item() == 0.0  # recipe's existing K -> C transform
    assert reader.query == reki.resolve_parameter("cedarkit.t2m").query


def test_python_plot_loads_through_provider(monkeypatch):
    """A legacy Python plot can use the provider DataLoader adapter."""
    reader = _Reader(xr.DataArray([[273.15] * 3] * 3, dims=("latitude", "longitude"), attrs={"units": "K"}))
    queries = []
    original_sel = reader.sel
    reader.sel = lambda query: queries.append(query) or original_sel(query)
    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: reader)
    result = load_t_dew_t(
        DataLoader(provider=RekiProvider(reki.SourceSpec("local", args=("fixture",)))),
        pd.Timestamp("2026-01-01"), pd.Timedelta(hours=6), 850,
    )
    assert result.level == 850
    assert [query.parameter for query in queries] == ["t", "DPT"]
    assert all(query.level == 850 for query in queries)


def test_t2m_recipe_provider_render_matches_legacy_data(monkeypatch, mock_data_source, start_time, forecast_time, tmp_path):
    """Provider pilot preserves raw fields and completes a render smoke test."""
    engine = get_recipe_engine()
    recipe_path = Path(__file__).parents[2] / "cedar_graph" / "recipes" / "cn" / "t2m.yaml"
    module = engine.build_module(engine.load_recipe(recipe_path))
    legacy_loader = DataLoader(data_source=mock_data_source)
    legacy = module.load_data(legacy_loader, start_time, forecast_time)

    class Reader:
        query = None
        def sel(self, query):
            self.query = query
            return self
        def one(self):
            return _Field(mock_data_source.retrieve(t_2m_info, start_time, forecast_time))

    reader = Reader()
    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: reader)
    provider = RekiProvider(reki.SourceSpec("local", args=("fixture",)))
    provided = module.load_data(DataLoader(provider=provider), start_time, forecast_time)
    xr.testing.assert_identical(provided.t2m, legacy.t2m)
    metadata = module.PlotMetadata(
        system_name="CMA-GFS", start_time=start_time, forecast_time=forecast_time,
    )
    output = tmp_path / "t2m-provider.png"
    module.plot(provided, metadata).save(output)
    assert output.exists() and output.stat().st_size > 0


def test_recipe_query_is_source_neutral_for_catalog_local_and_cmadaas_mock(monkeypatch):
    """A catalog source changes provider context, never the recipe query.

    The CMADaaS binding is intentionally mocked: this is the deterministic
    offline gate while a live service remains an optional integration test.
    """
    catalog = reki.load_catalog(plugins=False, user=False)
    local = catalog.resolve("CMA-GFS").source
    remote = catalog.resolve("CMA-GFS-CMADaaS").source
    calls = []
    readers = []

    def fake_from_source(spec, **kwargs):
        calls.append((spec, kwargs))
        reader = (_DirectReader if spec.name == "cmadaas" else _Reader)(
            xr.DataArray([[273.15]], dims=("latitude", "longitude"), attrs={"units": "K"})
        )
        readers.append(reader)
        return reader

    monkeypatch.setattr(reki, "from_source", fake_from_source)
    engine = get_recipe_engine()
    recipe_path = Path(__file__).parents[2] / "cedar_graph" / "recipes" / "cn" / "t2m.yaml"
    module = engine.build_module(engine.load_recipe(recipe_path))
    start_time = pd.Timestamp("2026-01-01")
    forecast_time = pd.Timedelta(hours=6)

    for source in (local, remote):
        result = module.load_data(
            DataLoader(provider=RekiProvider(source)), start_time, forecast_time,
        )
        assert result.t2m.item() == 0.0

    assert calls[0][0] == local
    assert calls[1][0] == remote
    assert calls[0][1] == {"start_time": start_time, "forecast_time": forecast_time}
    assert calls[1][1] == {
        "parameter": "TEM", "level_type": 103, "level": 2,
        "start_time": start_time, "forecast_time": forecast_time,
    }
    assert readers[0].query == reki.resolve_parameter("cedarkit.t2m").query
    assert readers[1].sel_calls == 0

    rain_recipe = engine.load_recipe(
        Path(__file__).parents[2] / "cedar_graph" / "recipes" / "cn" / "rain_wind_10m.yaml"
    )
    rain = rain_recipe.data["rain"]
    u_10m = rain_recipe.data["u_10m"]
    v_10m = rain_recipe.data["v_10m"]
    assert RECIPE_FIELDS[rain.field].to_field_query() == reki.resolve_parameter("cedarkit.rain").query
    assert RECIPE_FIELDS[u_10m.field].to_field_query(
    ) == reki.resolve_parameter("cedarkit.u").query
    assert (u_10m.level.first_level_type, u_10m.level.first_level) == (103, 10)
    assert (v_10m.level.first_level_type, v_10m.level.first_level) == (103, 10)


def test_recipe_v2_plan_has_stable_identity_and_matches_local_and_cmadaas_mock(monkeypatch):
    """Exercise the complete Recipe v2/PlotPlan direct-result route offline."""
    catalog = reki.load_catalog(plugins=False, user=False)
    local = catalog.resolve("CMA-GFS").source
    remote = catalog.resolve("CMA-GFS-CMADaaS")
    calls = []

    def fake_from_source(spec, **kwargs):
        calls.append((spec, kwargs))
        if spec.name == "cmadaas":
            code_to_number = {"TEM": 0, "PRE": 8, "WIU": 2, "WIV": 3}
            return _DirectReader(_recipe_fixture(
                code_to_number[kwargs["parameter"]], kwargs["forecast_time"],
            ))
        return _RecipeLocalReader(kwargs["forecast_time"])

    monkeypatch.setattr(reki, "from_source", fake_from_source)
    recipe_path = Path(__file__).parents[2] / "cedar_graph" / "recipes" / "cn"
    context = CompileContext(
        start_time="2026-01-01T00:00Z", forecast_time="24h",
    )
    loaded = load_recipe(recipe_path / "wind_10m.yaml")
    registry = OpRegistry.builtins()
    registry.register("wind_speed", lambda u, v: np.sqrt(u * u + v * v), kind="compute", input_count=2)
    plan = compile_recipe(loaded, context, registry=registry)

    # Plans depend only on the recipe/context; provider source identity and
    # CMADaaS codes do not enter their stable JSON representation.
    assert plan.to_dict() == compile_recipe(loaded, context, registry=registry).to_dict()
    reads = [node.request for node in plan.nodes if node.kind == "read"]
    assert [request.parameter_id for request in reads] == [
        "cedarkit.u", "cedarkit.v",
    ]
    assert [request.time_binding.forecast_time for request in reads] == ["P1DT0H0M0S"] * 2

    local_result = plan.execute(RekiProvider(local), registry=registry).outputs
    remote_provider = RekiProvider(remote)
    remote_result = plan.execute(remote_provider, registry=registry).outputs

    for name in ("u_10m", "v_10m", "ws_10m"):
        xr.testing.assert_allclose(remote_result[name], local_result[name])
        assert remote_result[name].dims == local_result[name].dims
        assert remote_result[name].coords.identical(local_result[name].coords)
        assert remote_result[name].attrs["units"] == local_result[name].attrs["units"]
    assert remote_result["u_10m"].attrs["cmadaas_parameter"] == "WIU"
    assert [trace.external_parameter for trace in remote_provider.trace] == [
        "WIU", "WIV",
    ]
    assert all(spec.name != "cmadaas" or "data_code" not in kwargs for spec, kwargs in calls)


def test_time_diff_recipe_binds_current_and_previous_times_for_both_offline_providers(monkeypatch):
    """Time differences make both source-neutral requests visible and bound."""
    catalog = reki.load_catalog(plugins=False, user=False)

    def fake_from_source(spec, **kwargs):
        if spec.name == "cmadaas":
            assert kwargs["parameter"] == "TEM"
            return _DirectReader(_recipe_fixture(0, kwargs["forecast_time"]))
        return _RecipeLocalReader(kwargs["forecast_time"])

    monkeypatch.setattr(reki, "from_source", fake_from_source)
    recipe = load_recipe({
        "api_version": "cedarkit.plots/v2", "kind": "PlotRecipe",
        "metadata": {"name": "test.t2m_time_diff"},
        "spec": {
            "params": {}, "domain": {"default": "x", "area": "x"},
            "data": {"result": {"field": {"parameter": "cedarkit.t2m"},
                                "transforms": [{"op": "time_diff", "args": ["12h"]}]}},
            "layers": [{"field": "result", "style": "test"}],
            "title": {"graph_name": "test"},
        },
    })
    plan = compile_recipe(recipe, CompileContext(start_time="2026-01-01T00:00Z", forecast_time="24h"))
    times = [node.request.time_binding.forecast_time for node in plan.nodes if node.kind == "read"]
    assert times == ["P1DT0H0M0S", "P0DT12H0M0S"]

    local_value = plan.execute(RekiProvider(catalog.resolve("CMA-GFS").source)).outputs["result"]
    remote_value = plan.execute(RekiProvider(catalog.resolve("CMA-GFS-CMADaaS"))).outputs["result"]
    xr.testing.assert_allclose(remote_value, local_value)
