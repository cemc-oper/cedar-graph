---
mystnb:
  execution_mode: 'off'
---

# 快速绘图

{func}`cedar_graph.quickplot.quick_plot` 按产品 ID 选择 v3 workflow，
用 reki 目录解析数据源并运行编译、数据处理和渲染。内置配方位于
`cedar_graph/recipes/workflow/cn/`；`cn.shr.default` 等五个原 Python
产品也使用同一条 workflow。产品清单见 {doc}`../api/recipes`。

## 默认范围下的 2 m 温度

```python
from cedar_graph.quickplot import quick_plot

quick_plot(
    plot_type="cn.t2m",
    system_name="CMA-GFS",
    start_time="2024073000",
    forecast_time="48h",
)
```

`start_time` 支持 `pd.Timestamp` 对象或 pandas 可解析的时间字符串。
`forecast_time` 支持 `pd.Timedelta` 对象或 `"24h"` 这样的字符串。

## 自定义区域的 10 m 风场

需要画到子区域时，配合 `area_name` 与
{class}`cedarkit.plots.types.AreaRange` 即可：

```python
from cedar_graph.quickplot import quick_plot
from cedarkit.plots.types import AreaRange

quick_plot(
    plot_type="cn.wind_10m",
    system_name="CMA-MESO",
    start_time="2024073000",
    forecast_time="48h",
    area_name="NorthEast",
    area_range=AreaRange.from_tuple((108, 137, 37, 55)),
)
```

## 带参数的图种

配方声明的参数（见 {doc}`recipe`）作为 `quick_plot` 的关键字参数
传入，例如 K 指数 + 风场的风场层次、降水图形的降水时段：

```python
quick_plot(
    plot_type="cn.kidx_wind",
    system_name="CMA-GFS",
    start_time="2024073000",
    forecast_time="48h",
    wind_level=850.0,          # 必需参数
)

quick_plot(
    plot_type="cn.rain_wind_10m",
    system_name="CMA-GFS",
    start_time="2024073000",
    forecast_time="48h",
    interval="24h",            # 降水时段
)
```

## 不在 CMA-HPC 时

在 CMA-HPC 之外，可按 {doc}`manual_plot` 使用
{class}`cedar_graph.testing.MockDataSource` 执行相同的产品。
