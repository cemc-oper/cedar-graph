---
mystnb:
  execution_mode: 'off'
---

# `cedar_graph.plots`

`cedar_graph.plots.cn` 下保留的是 **Python 逃生舱**图形——诊断逻辑
超出配方表达能力（设计文档 D6）的 5 个图种。其余 13 个图种已由
`cedar_graph/recipes/cn/` 下的 YAML 配方驱动（见
{doc}`recipes` 与 {doc}`../tutorials/recipe`）。

逃生舱模块与配方适配器对外暴露相同的三件套接口：
`PlotMetadata`、`load_data`、`plot`（部分模块另有 `PlotData` 与
自定义 `check_available`）。

## 诊断图（Python 逃生舱）

### `cn.div_wind`（散度 + 风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.div_wind.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.pte_wind`（假相当位温差 + 风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.pte_wind.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.qv_div`（水汽通量散度）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.qv_div.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.shr`（垂直风切变）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.shr.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.t_dew_t`（温度 − 露点温度）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.t_dew_t.default
   :members:
   :undoc-members:
   :show-inheritance:
```
