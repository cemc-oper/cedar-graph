import pandas as pd
import pytest
import xarray as xr
from pathlib import Path

import reki
from cedar_graph.data import DataLoader, RekiProvider
from cedar_graph.data.field_info import t_2m_info
from cedar_graph.recipes.engine import RECIPE_FIELDS, get_recipe_engine
from cedar_graph.plots.cn.t_dew_t.default import load_data as load_t_dew_t
from cedarkit.plots.plan.nodes import RequestKey, TimeBinding
from cedarkit.plots.plan.provider import BoundFieldRequest


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
        "parameter": "TEM", "level_type": "heightAboveGround", "level": 2,
        "start_time": pd.Timestamp("2026-01-01"), "forecast_time": pd.Timedelta(hours=6),
    })]
    assert provider.trace[-1].dataset_id == "cma_gfs_gmf_cmadaas"
    assert provider.trace[-1].catalog_origin == "builtin"
    assert provider.trace[-1].external_parameter == "TEM"


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
        "parameter": "TEM", "level_type": "heightAboveGround", "level": 2,
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
