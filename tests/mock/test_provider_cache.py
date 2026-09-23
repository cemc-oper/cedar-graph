import reki

from cedar_graph.data import RekiProvider


class _Field:
    def to_xarray(self):
        import xarray as xr
        return xr.DataArray([1.0])


class _Selected:
    def one(self):
        return _Field()


class _Reader:
    def sel(self, query):
        return _Selected()


def test_provider_reuses_equivalent_legacy_loads(monkeypatch):
    calls = []
    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: calls.append((args, kwargs)) or _Reader())
    provider = RekiProvider(reki.SourceSpec("local", args=("fixture",)))
    query = reki.FieldQuery(parameter="t2m")

    first = provider.load(query, start_time="2026071600", forecast_time="24h", parameter_id="cedarkit.t2m")
    second = provider.load(query, start_time="2026071600", forecast_time="24h", parameter_id="cedarkit.t2m")

    assert len(calls) == 1
    assert first.identical(second)
    assert provider.cache_info == {"hits": 1, "misses": 1, "entries": 1}


def test_provider_close_releases_cache_and_rejects_new_reads(monkeypatch):
    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: _Reader())
    provider = RekiProvider(reki.SourceSpec("local", args=("fixture",)))
    provider.load(reki.FieldQuery(parameter="t2m"), parameter_id="cedarkit.t2m")
    assert provider.cache_info["entries"] == 1
    provider.close()
    assert provider.cache_info["entries"] == 0
    import pytest
    with pytest.raises(RuntimeError, match="closed"):
        provider.load(reki.FieldQuery(parameter="t2m"), parameter_id="cedarkit.t2m")


def test_fetch_many_reuses_cached_field_and_traces_each_consumer(monkeypatch):
    from cedarkit.plots.plan.nodes import RequestKey, TimeBinding
    from cedarkit.plots.plan.provider import BoundFieldRequest

    calls = []
    monkeypatch.setattr(reki, "from_source", lambda *args, **kwargs: calls.append(1) or _Reader())
    provider = RekiProvider(reki.SourceSpec("local", args=("fixture",)))
    key = RequestKey(provider_slot="default", parameter_id="cedarkit.t2m",
                     query=reki.FieldQuery(parameter="t2m"),
                     time_binding=TimeBinding("2026-07-16", "24h"))
    first = BoundFieldRequest(node_id="first", key=key, origin="test")
    second = BoundFieldRequest(node_id="second", key=key, origin="test")
    values = provider.fetch_many((first, second))
    assert len(values) == 2 and values[0].identical(values[1])
    assert len(calls) == 1
    assert [item.node_id for item in provider.trace] == ["first", "second"]
    assert [item.status for item in provider.trace] == ["ok", "cached"]
