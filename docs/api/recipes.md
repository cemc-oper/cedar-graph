---
mystnb:
  execution_mode: 'off'
---

# `cedar_graph.recipes`

CEMC 业务图形的 YAML 配方库。`recipes/cn/` 下 13 个配方覆盖常规、
诊断与降水图种，由 quick_plot 装载器优先于 Python 模块加载。
配方编写指南见 {doc}`../tutorials/recipe`。

## 配方清单

| plot_type | 配方文件 | 图种 | 参数 |
|---|---|---|---|
| `cn.t2m` | `recipes/cn/t2m.yaml` | 2 米温度 | — |
| `cn.rh2m` | `recipes/cn/rh2m.yaml` | 2 米相对湿度 | — |
| `cn.h_500_psl` | `recipes/cn/h_500_psl.yaml` | 500 hPa 高度场 + 海平面气压 | — |
| `cn.h_500_wind_850` | `recipes/cn/h_500_wind_850.yaml` | 500 hPa 高度场 + 850 hPa 风场 | — |
| `cn.wind_10m` | `recipes/cn/wind_10m.yaml` | 10 米风场 | — |
| `cn.cdbz` | `recipes/cn/cdbz.yaml` | 雷达组合反射率 | — |
| `cn.kidx_wind` | `recipes/cn/kidx_wind.yaml` | K 指数 + 风场 | `wind_level`（必需） |
| `cn.cape_wind` | `recipes/cn/cape_wind.yaml` | CAPE + 风场 | `wind_level`（必需） |
| `cn.cin_wind` | `recipes/cn/cin_wind.yaml` | CIN + 风场 | `wind_level`（必需） |
| `cn.bli_wind` | `recipes/cn/bli_wind.yaml` | 最优抬升指数 + 风场 | `wind_level`（必需） |
| `cn.rain_24h` | `recipes/cn/rain_24h.yaml` | 24 小时降水 | `interval`（缺省 24h） |
| `cn.rain_wind_10m` | `recipes/cn/rain_wind_10m.yaml` | 降水 + 10 米风场 | `interval`（必需） |
| `cn.prep_24h` | `recipes/cn/prep_24h.yaml` | 24 小时多相态降水 | `interval`（缺省 24h） |

## 包接口

```{eval-rst}
.. automodule:: cedar_graph.recipes
   :members:
   :undoc-members:
   :show-inheritance:
```

## 配方引擎配置

`cedar_graph.recipes.engine` 把业务部件接入 cedarkit-plots 的
业务无关引擎：cemc 要素字段注册表（`FIELD_INFOS`）、诊断 compute op
（`wind_speed`、`prep_classify`）与默认样式注册表。

```{eval-rst}
.. automodule:: cedar_graph.recipes.engine
   :members:
   :undoc-members:
   :show-inheritance:
```
