---
mystnb:
  execution_mode: 'off'
---

# `cedar_graph.data`

```{eval-rst}
.. automodule:: cedar_graph.data
   :members:
   :undoc-members:
   :show-inheritance:
```

## 数据源（Source）

```{eval-rst}
.. automodule:: cedar_graph.data.source
   :members:
   :undoc-members:
   :show-inheritance:
```

## 数据加载器（Loader）

```{eval-rst}
.. automodule:: cedar_graph.data.loader
   :members:
   :undoc-members:
   :show-inheritance:
```

## Reki provider

`RekiProvider` binds an immutable `reki.SourceSpec` and runtime times to a
source-neutral `BoundFieldRequest`.  Existing `DataSource` and `DataLoader`
remain supported. A `DataLoader(provider=...)` adapts legacy `FieldInfo`
values through `FieldInfo.to_field_query()`.

For a selectable local GRIB source, the provider keeps the established
`from_source(...).sel(FieldQuery).one()` / `one_or_none()` path.  A CMADaaS
`model_grid` source advertises a direct-result capability instead: before it
constructs the source, the provider combines the stable `parameter_id`, its
concrete `FieldQuery`, and the request time with
`reki.bind_cmadaas_request()`.  The returned in-memory field is normalized and
validated directly; it is never selected again with `.sel()`.

Recipes and `PlotPlan` therefore remain source-neutral: they contain neither a
CMADaaS code, catalog data code, source name, nor credentials.  Resolve the
catalog record at the execution boundary and pass it to the provider:

```python
import reki
from cedar_graph.data import RekiProvider

dataset = reki.load_catalog().resolve("CMA-GFS-CMADaaS")
provider = RekiProvider(dataset, region={"min_lon": 116, "max_lon": 117,
                                         "min_lat": 39, "max_lat": 40})
result = plan.execute(provider)
```

`fetch_many()` preserves request order and falls back to individual CMADaaS
requests when the service has no equivalent batch API. `check_many()` returns
`"unknown"` for a direct-result source because CMADaaS has no metadata-only
check; it does not download a grid merely to determine availability. The
public `ProviderTrace` records catalog origin, parameter identity, external
code, time and status, but excludes client configuration and authentication.

```{eval-rst}
.. automodule:: cedar_graph.data.provider
   :members:
```

## 字段元信息（Field info）

```{eval-rst}
.. automodule:: cedar_graph.data.field_info
   :members:
   :undoc-members:
   :show-inheritance:
```

## 数据算子（Operator）

```{eval-rst}
.. automodule:: cedar_graph.data.operator
   :members:
   :undoc-members:
   :show-inheritance:
```

## 绘图元信息（Metadata）

```{eval-rst}
.. automodule:: cedar_graph.metadata
   :members:
   :undoc-members:
   :show-inheritance:
```
