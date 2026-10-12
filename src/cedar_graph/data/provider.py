"""Thin bridge binding cedar-graph field requirements to reki sources."""
from __future__ import annotations
from dataclasses import dataclass, replace
import json
import re
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

import xarray as xr
import pandas as pd
import reki

from cedarkit.plots.workflow.plan.model import BoundFieldRequest, public_request_from_field_request


@dataclass(frozen=True)
class ProviderTrace:
    """Public, credential-free evidence for one provider request."""

    node_id: str
    dataset_id: str | None
    catalog_origin: str | None
    provider: str
    parameter_id: str
    external_parameter: str | None
    level_type: Any
    level: Any
    start_time: str | None
    forecast_time: str | None
    status: str
    duration_seconds: float
    error_code: str | None = None

class RekiProvider:
    """Load strict reki fields from a reusable :class:`reki.SourceSpec`."""
    def __init__(self, source_spec: reki.SourceSpec | Any, *,
                 region: Mapping[str, Any] | None = None):
        """Create a provider from a SourceSpec or catalog ResolvedDataset."""
        self.dataset_id = None
        self.catalog_origin = None
        if hasattr(source_spec, "source") and hasattr(source_spec, "record"):
            self.dataset_id = source_spec.record.dataset_id
            self.catalog_origin = source_spec.origin
            source_spec = source_spec.source
        if not isinstance(source_spec, reki.SourceSpec):
            raise TypeError("source_spec must be a reki.SourceSpec")
        self.source_spec = source_spec
        self.region = None if region is None else dict(region)
        self.trace: list[ProviderTrace] = []
        self._field_cache: dict[tuple[Any, ...], xr.DataArray | None] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._closed = False
        self._query_snapshot = None

    @classmethod
    def from_query_catalog(cls, snapshot, dataset: str, *, native_parameters: Mapping[str, str],
                           member_roles: Mapping[str, str] | None = None,
                           candidate_paths=(), local_config_version: str | None = None,
                           local_config_dir: Path | None = None, index_policy: str = "off",
                           index_dir: Path | None = None, hash_resources: bool = False,
                           registry_sha256: str | None = None):
        """Create a public-query provider while keeping legacy SourceSpec callers intact."""
        from reki.catalog.query_binding import CatalogSnapshot
        from reki.query_collection import CollectionSession

        if not isinstance(snapshot, CatalogSnapshot):
            raise TypeError("snapshot must be a CatalogSnapshot")
        resolved = snapshot.catalog.resolve(dataset)
        provider = cls(resolved)
        provider._query_snapshot = snapshot
        provider._native_parameters = dict(native_parameters)
        provider._member_roles = None if member_roles is None else dict(member_roles)
        provider._candidate_paths = tuple(Path(path) for path in candidate_paths)
        provider._local_config_version = local_config_version
        provider._local_config_dir = local_config_dir
        provider._index_policy = index_policy
        provider._index_dir = index_dir
        provider._registry_sha256 = registry_sha256
        provider._hash_resources = hash_resources
        provider._collection_session = CollectionSession(index_policy=index_policy, index_dir=index_dir,
                                                          hash_resources=hash_resources)
        return provider

    def close(self) -> None:
        """Release task-owned cached arrays and traces; leave the source alone."""
        self._field_cache.clear()
        self.trace.clear()
        if self._query_snapshot is not None:
            self._collection_session.close()
        self._closed = True

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("provider is closed")

    @property
    def cache_info(self) -> Mapping[str, int]:
        """Counters and entries for this provider's task-local field cache."""
        if self._query_snapshot is not None:
            info = self._collection_session.cache_info()
            return {"hits": info.value_hits, "misses": info.value_misses,
                    "entries": info.resources}
        return {"hits": self._cache_hits, "misses": self._cache_misses, "entries": len(self._field_cache)}

    @staticmethod
    def _field_cache_key(query, start_time, forecast_time, cardinality, parameter_id):
        query_key = json.dumps({
            "parameter": query.parameter, "level_type": query.level_type,
            "level": query.level, "step_type": query.step_type,
            "time_range": query.time_range, "member": query.member,
            "extra": dict(query.extra),
        }, sort_keys=True, default=str)
        return (query_key, str(start_time), str(forecast_time), cardinality, parameter_id)

    def _capability(self):
        """Read the source-declared capability without mutating the source."""
        return reki.source_capability(self.source_spec)

    @staticmethod
    def _bindings(*, start_time=None, forecast_time=None):
        return {key: value for key, value in {
            "start_time": start_time, "forecast_time": forecast_time,
        }.items() if value is not None}

    def _selectable_binding(self, query, *, start_time=None, forecast_time=None):
        """Bind a mounted ensemble member to both its file and GRIB field."""
        bindings = self._bindings(start_time=start_time, forecast_time=forecast_time)
        if self.source_spec.name != "local" or query.member is None:
            return bindings, query
        member = query.member
        if isinstance(member, bool) or not (isinstance(member, int) and member >= 0
                                             or isinstance(member, str) and re.fullmatch(r"m?\d+", member)):
            raise ValueError(f"local ensemble member must be a non-negative number or mNNN ID: {member!r}")
        number = int(member.lstrip("m")) if isinstance(member, str) else member
        bindings["number"] = number
        return bindings, replace(query, member=number)

    @staticmethod
    def _request_times(key):
        """Decode v3 request times for the reki source."""
        start = pd.Timestamp(key.start_time) if key.start_time is not None else None
        if key.forecast_time is None:
            forecast = None
        else:
            try:
                forecast = pd.Timedelta(key.forecast_time)
            except (TypeError, ValueError):
                forecast = pd.Timestamp(key.forecast_time)
        return start, forecast

    def _append_trace(self, request: BoundFieldRequest, *, status: str,
                      duration: float, external_parameter: str | None = None,
                      error_code: str | None = None) -> None:
        key = request.key
        start_time, forecast_time = self._request_times(key)
        self.trace.append(ProviderTrace(
            node_id=request.node_id, dataset_id=self.dataset_id,
            catalog_origin=self.catalog_origin, provider=self.source_spec.name,
            parameter_id=key.parameter_id, external_parameter=external_parameter,
            level_type=key.query.level_type, level=key.query.level,
            start_time=None if start_time is None else str(start_time),
            forecast_time=None if forecast_time is None else str(forecast_time),
            status=status, duration_seconds=duration, error_code=error_code,
        ))

    # WorkflowPlan provider contract --------------------------------------------
    def fetch(self, request: BoundFieldRequest):
        """Fetch one compiled request using its concrete time binding."""
        self._ensure_open()
        if self._query_snapshot is not None:
            return self._fetch_public_many((request,))[0]
        capability = self._capability()
        if capability is not None and capability.direct_result:
            start_time, forecast_time = self._request_times(request.key)
            cache_key = self._field_cache_key(request.key.query, start_time, forecast_time,
                                              request.key.cardinality, request.key.parameter_id)
            if cache_key in self._field_cache:
                self._cache_hits += 1
                value = self._field_cache[cache_key]
                self._append_trace(request, status="cached", duration=0)
                return None if value is None else value.copy(deep=False)
            self._cache_misses += 1
            value = self._fetch_direct(request)
            self._field_cache[cache_key] = value
            return value.copy(deep=False)
        return self._fetch_selectable(request)

    def _fetch_selectable(self, request: BoundFieldRequest):
        started = perf_counter()
        start_time, forecast_time = self._request_times(request.key)
        cache_key = self._field_cache_key(request.key.query, start_time, forecast_time,
                                          request.key.cardinality, request.key.parameter_id)
        if cache_key in self._field_cache:
            self._cache_hits += 1
            value = self._field_cache[cache_key]
            self._append_trace(request, status="cached", duration=0)
            return None if value is None else value.copy(deep=False)
        self._cache_misses += 1
        try:
            bindings, selected_query = self._selectable_binding(
                request.key.query, start_time=start_time, forecast_time=forecast_time)
            selected = reki.from_source(self.source_spec, **bindings).sel(selected_query)
            cardinality = request.key.cardinality
            if cardinality == "one":
                field = selected.one()
            elif cardinality == "first":
                field = selected.first()
            elif cardinality == "all":
                # Ensemble plans issue one request per member; this marks an
                # optional member lookup, not a multi-field result.
                field = selected.one_or_none()
            else:
                raise ValueError(f"unsupported field cardinality {cardinality!r}")
            value = None if field is None else field.to_xarray()
        except Exception as exc:
            self._append_trace(request, status="error", duration=perf_counter() - started,
                               error_code=getattr(exc, "code", type(exc).__name__))
            raise
        self._field_cache[cache_key] = value
        self._append_trace(request, status="missing" if value is None else "ok",
                           duration=perf_counter() - started)
        return None if value is None else value.copy(deep=False)

    def _fetch_direct(self, request: BoundFieldRequest):
        """Bind a high-level request before source construction; never select it."""
        started = perf_counter()
        start_time, forecast_time = self._request_times(request.key)
        try:
            bound = reki.bind_cmadaas_request(
                self.source_spec, parameter_id=request.key.parameter_id,
                query=request.key.query,
                start_time=start_time,
                forecast_time=forecast_time,
                member=request.key.query.member,
                region=self.region,
            )
            result = reki.from_source(self.source_spec, **bound.dynamic_source_kwargs()).to_xarray()
            if not isinstance(result, xr.DataArray):
                raise TypeError("CMADaaS model_grid must return one xarray.DataArray")
            result = reki.normalize_data_array(result, source=self.source_spec)
            reki.validate_data_array(result, mode="raise")
            result = result.rename(request.key.parameter_id)
            result.attrs = dict(result.attrs)
            result.attrs["cmadaas_parameter"] = bound.parameter
        except Exception as exc:
            self._append_trace(request, status="error", duration=perf_counter() - started,
                               error_code=getattr(exc, "code", type(exc).__name__))
            raise
        self._append_trace(request, status="ok", duration=perf_counter() - started,
                           external_parameter=bound.parameter)
        return result

    def _public_plan(self, request: BoundFieldRequest):
        from reki.catalog.query_binding import plan_source_binding

        key = request.key
        public = public_request_from_field_request(
            request, dataset=self.dataset_id,
            native_parameter=self._native_parameters.get(key.parameter_id),
            member_roles=self._member_roles)
        plan = plan_source_binding(public.query, snapshot=self._query_snapshot,
                                   local_config_version=self._local_config_version)
        return public, plan

    def _public_candidates(self, plan):
        if self._candidate_paths:
            return self._candidate_paths
        from reki.query_locator import _path
        return (Path(_path(plan, plan.query.to_dict(), local_config_dir=self._local_config_dir)),)

    def _fetch_public_many(self, requests):
        from reki.query_collection import CollectionRequest
        from reki.query_cmadaas import read_frozen_cmadaas

        self._ensure_open()
        requests = tuple(requests)
        if not requests:
            return []
        started = perf_counter()
        try:
            prepared = [self._public_plan(request) for request in requests]
            if all(plan.binding.kind == "local" for _, plan in prepared):
                jobs = (CollectionRequest(plan, self._public_candidates(plan), self._native_parameters,
                                          self._member_roles, public.policy["missing"],
                                          self._local_config_dir)
                        for public, plan in prepared)
                results = self._collection_session.read_many(jobs)
                values = []
                for result in results:
                    if result.data is None:
                        values.append(None)
                    elif len(result.fields) != 1:
                        raise ValueError("workflow read requires one public field")
                    else:
                        field = result.fields[0]
                        value = field.data.copy(deep=True)
                        value.attrs = dict(value.attrs)
                        value.attrs["source_reference"] = field.reference.to_dict()
                        values.append(value)
            elif all(plan.binding.kind == "cmadaas" for _, plan in prepared):
                if self._registry_sha256 is None:
                    raise ValueError("CMADaaS public reads require registry_sha256")
                values = []
                for _, plan in prepared:
                    result = read_frozen_cmadaas(plan, registry_sha256=self._registry_sha256)
                    value = result.data.rename(plan.query.parameter)
                    value.attrs = dict(value.attrs)
                    value.attrs["cmadaas_parameter"] = result.execution.request.parameter
                    values.append(value)
            else:
                raise ValueError("one provider batch cannot mix source kinds")
        except Exception as exc:
            for request in requests:
                self._append_trace(request, status="error", duration=perf_counter() - started,
                                   error_code=getattr(exc, "code", type(exc).__name__))
            raise
        for request, value in zip(requests, values):
            self._append_trace(request, status="missing" if value is None else "ok",
                               duration=perf_counter() - started)
        return values

    def _check_public_many(self, requests):
        from cedarkit_query import QueryError
        from reki.query_locator import locate_fields

        statuses = []
        for request in requests:
            try:
                _, plan = self._public_plan(request)
                if plan.binding.kind == "cmadaas":
                    from reki.query_cmadaas import plan_frozen_cmadaas
                    if self._registry_sha256 is None:
                        statuses.append("invalid")
                        continue
                    plan_frozen_cmadaas(plan, registry_sha256=self._registry_sha256)
                report = locate_fields(plan, native_parameters=self._native_parameters,
                                       member_roles=self._member_roles,
                                       local_config_dir=self._local_config_dir,
                                       index_dir=self._index_dir, index_policy=self._index_policy,
                                       missing="partial", hash_resources=self._hash_resources,
                                       candidate_paths=self._candidate_paths or None)
                if report.status == "unknown":
                    statuses.append("unknown")
                elif any(item.verification != "field_confirmed" for item in report.items):
                    statuses.append("missing")
                else:
                    statuses.append("available")
            except QueryError as exc:
                statuses.append({"multiple_matches": "multiple", "unsupported": "invalid",
                                 "invalid_query": "invalid", "unmapped_parameter": "invalid",
                                 "unknown_parameter": "invalid"}.get(exc.code, "provider_error"))
            except Exception:
                statuses.append("provider_error")
        return statuses

    def fetch_many(self, requests):
        """Fetch in order through the same cache and trace path as fetch."""
        requests = tuple(requests)
        if self._query_snapshot is not None:
            return self._fetch_public_many(requests)
        return [self.fetch(request) for request in requests]

    def check_many(self, requests):
        """Check metadata when supported; direct-result sources are unknown."""
        self._ensure_open()
        if self._query_snapshot is not None:
            return self._check_public_many(tuple(requests))
        capability = self._capability()
        if capability is not None and not capability.metadata_only:
            return ["unknown" for _ in requests]
        result = []
        for request in requests:
            start_time, forecast_time = self._request_times(request.key)
            kwargs, selected_query = self._selectable_binding(
                request.key.query, start_time=start_time, forecast_time=forecast_time)
            try:
                reader = reki.from_source(self.source_spec, **kwargs)
                selected = reader.sel(selected_query)
                # ``one_or_none`` is the strict metadata/cardinality boundary;
                # it does not call ``to_xarray`` or decode values.
                result.append("available" if selected.one_or_none() is not None else "missing")
            except Exception as exc:
                result.append("provider_error")
        return result
