"""Provider integration uses public declarations and v1 Query results only."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
import reki
from cedarkit_query import Query, QueryError
from cedar_graph.data import RekiProvider
from .test_public_query_provider import _fixture


def test_provider_metadata_cache_and_retained_evidence(tmp_path):
    source, _, request, _ = _fixture(tmp_path)
    provider=RekiProvider(source)
    try:
        assert provider.check_many((request,))==['available']
        values=provider.fetch_many((request,request))
        assert values[0].identical(values[1])
        assert provider.cache_info=={'hits':1,'misses':1,'entries':1}
        assert [t.status for t in provider.trace]==['ok','cached']
    finally:provider.close()
    assert provider.trace and provider.cache_info['entries']==0


def test_public_provider_rejects_unbound_workflow_times(tmp_path):
    source, _, request, _ = _fixture(tmp_path)
    request=replace(request,key=replace(request.key,start_time=None,forecast_time=None))
    with RekiProvider(source) as provider:
        with pytest.raises(QueryError, match='explicit times') as error:
            provider.fetch(request)
        assert error.value.code=='invalid_query'
        assert provider.trace[-1].error_code=='invalid_query'


def test_old_source_objects_are_rejected_before_source_construction(monkeypatch):
    monkeypatch.setattr(reki,'from_source',lambda *a,**k: (_ for _ in ()).throw(AssertionError('must not open')))
    with pytest.raises(QueryError,match='declaration mapping') as error:
        RekiProvider(SimpleNamespace(name='local',args=('fixture',),kwargs={}))
    assert error.value.code=='invalid_config'


def test_member_stays_in_public_query_without_mutating_source(tmp_path,monkeypatch):
    source, _, request, _ = _fixture(tmp_path)
    source={'kind':'local','dataset':'cma_geps','root':str(tmp_path)}
    calls=[]
    class Owner:
        def sel(self,queries):calls.extend(queries);return self
        def explain(self):return None
        def all(self):return []
        def close(self):pass
    monkeypatch.setattr(reki,'from_source',lambda declaration,**kw: Owner())
    request=replace(request,key=replace(request.key,query=Query({**request.key.query.to_dict(),'member':3})))
    with RekiProvider(source) as provider:assert provider.check_many((request,))==['missing']
    assert calls[0].member==3 and source=={'kind':'local','dataset':'cma_geps','root':str(tmp_path)}
