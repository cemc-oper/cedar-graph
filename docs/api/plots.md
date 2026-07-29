---
mystnb:
  execution_mode: 'off'
---

# `cedar_graph.plots`

`cedar_graph.plots.cn.<name>.default` 下的每一个绘图模块都对外暴露
相同的四个符号：`PlotMetadata`、`PlotData`、`load_data`、`plot`。

## 常规图

### `cn.t_2m`（2 米温度）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.t_2m.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.rh_2m`（2 米相对湿度）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.rh_2m.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.height_500_mslp`（500 hPa 高度场 + 海平面气压）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.height_500_mslp.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.height_500_wind_850`（500 hPa 高度场 + 850 hPa 风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.height_500_wind_850.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.wind_10m`（10 米风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.wind_10m.default
   :members:
   :undoc-members:
   :show-inheritance:
```

## 诊断图

### `cn.radar_reflectivity`（雷达组合反射率）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.radar_reflectivity.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.div_wind`（散度 + 风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.div_wind.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.k_wind`（K 指数 + 风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.k_wind.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.cape_wind`（CAPE + 风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.cape_wind.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.cin_wind`（CIN + 风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.cin_wind.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.bli_wind`（最优抬升指数 + 风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.bli_wind.default
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

## 降水图

### `cn.rain_24h`（24 小时降水）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.rain_24h.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.rain_wind_10m`（降水 + 10 米风场）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.rain_wind_10m.default
   :members:
   :undoc-members:
   :show-inheritance:
```

### `cn.prep_24h`（24 小时多相态降水）

```{eval-rst}
.. automodule:: cedar_graph.plots.cn.prep_24h.default
   :members:
   :undoc-members:
   :show-inheritance:
```
