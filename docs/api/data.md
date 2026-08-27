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

`RekiProvider` is the stage-1 bridge for new integrations. It binds an
immutable `reki.SourceSpec` and runtime times to a `reki.FieldQuery`; required
loads use `one()` while optional loads use `one_or_none()`. Existing
`DataSource` and `DataLoader` remain supported. A `DataLoader(provider=...)`
adapts legacy `FieldInfo` values through `FieldInfo.to_field_query()`.

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
