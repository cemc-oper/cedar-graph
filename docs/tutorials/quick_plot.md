---
mystnb:
  execution_mode: 'off'
---

# 快速绘图

{func}`cedar_graph.quickplot.quick_plot` 是在 CMA-HPC 上
最快速的画图方式。指定图种、业务系统名以及预报时间，
它内部会通过 {class}`~cedar_graph.data.LocalDataSource`
完成数据查找与读取。

## 默认范围下的 2 m 温度

```python
from cedar_graph.quickplot import quick_plot

quick_plot(
    plot_type="cn.t_2m.default",
    system_name="CMA-GFS",
    start_time="2024073000",
    forecast_time="48h",
)
```

`start_time` 既支持 `pd.Timestamp` 对象，也支持 GRIB 中常用的
紧凑形式 `"YYYYMMDDHH"` / `"YYYYMMDDHHMM"`。
`forecast_time` 支持 `pd.Timedelta` 对象或 `"24h"` 这样的字符串。

## 自定义区域的 10 m 风场

需要画到子区域时，配合 `area_name` 与
{class}`cedarkit.plots.types.AreaRange` 即可：

```python
from cedar_graph.quickplot import quick_plot
from cedarkit.plots.types import AreaRange

quick_plot(
    plot_type="cn.wind_10m.default",
    system_name="CMA-MESO",
    start_time="2024073000",
    forecast_time="48h",
    area_name="NorthEast",
    area_range=AreaRange.from_tuple((108, 137, 37, 55)),
)
```

## 不在 CMA-HPC 时

`quick_plot` 默认假设了 CMA-HPC 上的目录结构与配置。在
CMA-HPC 之外的环境，请改用 {doc}`manual_plot` 中介绍的方式直接
驱动 `load_data` 与 `plot`，并按需挑选数据源——例如本文档使用的
{class}`cedar_graph.testing.MockDataSource`。
