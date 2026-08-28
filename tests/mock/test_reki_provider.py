import pandas as pd
import pytest
import xarray as xr
from pathlib import Path

import reki
from cedar_graph.data import DataLoader, RekiProvider
from cedar_graph.data.field_info import t_2m_info
from cedar_graph.recipes.engine import get_recipe_engine
from cedar_graph.plots.cn.t_dew_t.default import load_data as load_t_dew_t


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


def test_provider_binds_times_and_uses_strict_api(monkeypatch):
    reader = _Reader(xr.DataArray([1], attrs={"units": "K"}))
    calls = []
    monkeypatch.setattr(reki, "from_source", lambda spec, **kwargs: calls.append((spec, kwargs)) or reader)
    provider = RekiProvider(reki.SourceSpec("local", args=("archive",)))
    result = provider.load(reki.FieldQuery(parameter="2t"), start_time=pd.Timestamp("2026-01-01"), forecast_time="6h")
    assert result.identical(reader.data)
    assert reader.query == reki.FieldQuery(parameter="2t")
    assert calls[0][1]["forecast_time"] == "6h"


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
