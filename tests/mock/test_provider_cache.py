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
