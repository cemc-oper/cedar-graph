"""Thin bridge binding cedar-graph field requirements to reki sources."""
from __future__ import annotations
from dataclasses import dataclass
import json
from time import perf_counter
from typing import Any, Mapping

import xarray as xr
import pandas as pd
import reki
from cedarkit_query import QueryError, SourceError

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
    query_report: dict[str, Any] | None = None
    field_identity: dict[str, Any] | None = None
    source_reference: dict[str, Any] | None = None

class RekiProvider:
    """Own a public reki source and adapt single fields for plotting.

    Source declarations use the public v1 Query/Dataset interface.
    """
    def __init__(self, source_spec: Mapping[str, Any], *,
                 context: Mapping[str, Any] | str | None = None, client=None,
                 region: Mapping[str, Any] | None = None):
        """Create a task-owned source; an injected service client stays caller-owned."""
        self.dataset_id = None
        self.catalog_origin = None
        self._query_source = None
        self._context = context
        if not isinstance(source_spec, Mapping):
            raise QueryError("invalid_config", "/source", "A public source declaration mapping is required")
        self._query_source = reki.from_source(source_spec, context=context, client=client)
        source_spec = dict(source_spec)
        self.dataset_id = source_spec.get("dataset")
        self.source_spec = source_spec
        self.region = None if region is None else dict(region)
        self.trace: list[ProviderTrace] = []
        self.query_reports: list[dict[str, Any]] = []
        self._evidence_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
        self._field_cache: dict[tuple[Any, ...], xr.DataArray | None] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._closed = False

    def close(self) -> None:
        """Release resources; public sources retain execution evidence snapshots."""
        if self._closed:
            return
        self._field_cache.clear()
        self._evidence_cache.clear()
        self._query_source.close()
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
        return {"hits": self._cache_hits, "misses": self._cache_misses, "entries": len(self._field_cache)}

    @staticmethod
    def _field_cache_key(query, start_time, forecast_time, cardinality, parameter_id):
        query_key = json.dumps(query.to_dict(), sort_keys=True, default=str)
        return (query_key, str(start_time), str(forecast_time), cardinality, parameter_id)

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
                      error_code: str | None = None, query_report=None,
                      field_identity=None, source_reference=None) -> None:
        key = request.key
        start_time, forecast_time = self._request_times(key)
        self.trace.append(ProviderTrace(
            node_id=request.node_id, dataset_id=self.dataset_id,
            catalog_origin=self.catalog_origin, provider=self.source_spec.get("kind", "unknown"),
            parameter_id=key.parameter_id, external_parameter=external_parameter,
            level_type=(field_identity or key.query.to_dict()).get("level_type"),
            level=(field_identity or key.query.to_dict()).get("level"),
            start_time=None if start_time is None else str(start_time),
            forecast_time=None if forecast_time is None else str(forecast_time),
            status=status, duration_seconds=duration, error_code=error_code,
            query_report=query_report, field_identity=field_identity,
            source_reference=source_reference,
        ))

    # WorkflowPlan provider contract --------------------------------------------
    def fetch(self, request: BoundFieldRequest):
        """Fetch one compiled request using its concrete time binding."""
        self._ensure_open()
        return self._fetch_public(request)

    def _public_selection(self, request):
        public = public_request_from_field_request(
            request, source=self.source_spec, context=self._context)
        return self._query_source.sel(public.queries)

    @staticmethod
    def _plot_array(dataset, *, parameter_id, report, identity, reference, metadata=None):
        """Select one variable and collapse only singleton business axes.

        Spatial axes, including one-point grids, remain intact. Scalar identity
        coordinates retain the actual time, step, member and vertical selection.
        """
        if not isinstance(dataset, xr.Dataset) or len(dataset.data_vars) != 1:
            raise QueryError("multiple_variables", "/result", "plotting requires exactly one Dataset variable")
        value = dataset[next(iter(dataset.data_vars))]
        axes = {"time", "step", "member", "pressure", "height_above_ground",
                "height_above_sea", "depth_below_land", "model_level"}
        for axis in axes.intersection(value.dims):
            if value.sizes[axis] != 1:
                raise QueryError("multiple_matches", "/result", "plotting requires singleton business axes",
                                 {"axis": axis, "size": value.sizes[axis]})
            value = value.isel({axis: 0}, drop=False)
        value = value.rename(parameter_id)
        value.attrs = {**dataset.attrs, **value.attrs,
                       "cedarkit_query_report": json.dumps(report, sort_keys=True),
                       "field_identity": json.dumps(identity, sort_keys=True),
                       "source_reference": json.dumps(reference, sort_keys=True)}
        for key in ("statistical_interval", "value_encoding"):
            if metadata is not None and key in metadata:
                value.attrs[key] = json.dumps(dict(metadata[key]), sort_keys=True)
        return value

    def _fetch_public(self, request):
        started = perf_counter()
        key = request.key
        cache_key = self._field_cache_key(key.query, key.start_time, key.forecast_time,
                                          key.cardinality, key.parameter_id)
        if cache_key in self._field_cache:
            self._cache_hits += 1
            value = self._field_cache[cache_key]
            self._append_trace(request, status="cached", duration=0,
                               **self._evidence_cache[cache_key])
            return None if value is None else value.copy(deep=True)
        self._cache_misses += 1
        evidence = {}
        try:
            selection = self._public_selection(request)
            if key.cardinality == "one":
                field = selection.one()
                report = field.report.to_dict()
            elif key.cardinality == "first":
                field = selection.first()
                report = None if field is None else field.report.to_dict()
            elif key.cardinality == "all":
                # Ensemble plans issue one optional member request at a time.
                fields = selection.all()
                report = fields.report.to_dict()
                if len(fields) > 1:
                    raise QueryError("multiple_matches", "/result", "optional member matched multiple fields")
                field = fields[0] if len(fields) else None
            else:
                raise ValueError(f"unsupported field cardinality {key.cardinality!r}")
            evidence = {"query_report": report}
            if report is not None:
                self.query_reports.append(report)
            if field is None:
                value = None
            else:
                identity = field.identity.to_dict()
                reference = json.loads(json.dumps(dict(field.metadata.get("source", {}))))
                evidence.update(field_identity=identity, source_reference=reference)
                value = self._plot_array(field.to_xarray(), parameter_id=key.parameter_id,
                                         report=report, identity=identity, reference=reference,
                                         metadata=field.metadata)
        except Exception as exc:
            failed_report = getattr(exc, "report", None)
            if failed_report is not None:
                evidence["query_report"] = failed_report.to_dict()
                self.query_reports.append(evidence["query_report"])
            self._append_trace(request, status="error", duration=perf_counter() - started,
                               error_code=getattr(exc, "code", type(exc).__name__), **evidence)
            raise
        self._field_cache[cache_key] = value
        self._evidence_cache[cache_key] = evidence
        self._append_trace(request, status="missing" if value is None else "ok",
                           duration=perf_counter() - started, **evidence)
        return None if value is None else value.copy(deep=True)

    def _check_public_many(self, requests):
        statuses = []
        for request in requests:
            try:
                selection = self._public_selection(request)
                # Service explain is static. File all scans headers, not values.
                selection.explain()
                if self.source_spec["kind"] == "cmadaas":
                    statuses.append("unknown")
                    continue
                fields = selection.all()
                count = len(fields)
                statuses.append("missing" if count == 0 else "multiple"
                                if count > 1 and request.key.cardinality != "first" else "available")
            except (QueryError, SourceError) as exc:
                statuses.append({"multiple_matches": "multiple", "no_match": "missing",
                                 "missing_fields": "missing", "resource_not_found": "missing",
                                 "unsupported": "invalid", "invalid_query": "invalid",
                                 "unmapped_parameter": "invalid", "unknown_parameter": "invalid"
                                 }.get(exc.code, "provider_error"))
        return statuses

    def fetch_many(self, requests):
        """Fetch in order through the same cache and trace path as fetch."""
        return [self.fetch(request) for request in requests]

    def check_many(self, requests):
        """Check metadata when supported; direct-result sources are unknown."""
        self._ensure_open()
        return self._check_public_many(tuple(requests))
