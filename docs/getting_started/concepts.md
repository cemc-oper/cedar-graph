---
mystnb:
  execution_mode: 'off'
---

# 核心概念

cedar-graph 的对外接口由若干互相协作的小组件构成。理解它们
有助于阅读现有的绘图模块，也方便添加新的图种。

## DataSource

{class}`~cedar_graph.data.DataSource` 描述了"如何根据
{class}`~cedar_graph.data.FieldInfo`、`start_time`、
`forecast_time` 取出某一个场"的能力。

cedar-graph 内置了两种实现：

- {class}`~cedar_graph.data.LocalDataSource`：在 CMA-HPC
  共享文件系统上通过 `reki.data_finder` 解析路径，
  使用 ecCodes 读取 GRIB2 字段。
- {class}`cedar_graph.testing.MockDataSource`：解析式生成
  合成场，本文档与 mock 测试都使用这一实现。

## DataLoader

{class}`~cedar_graph.data.DataLoader` 包装一个 `DataSource`，
对外暴露统一的 `load(field_info, start_time, forecast_time)`
方法。绘图模块只与 loader 交互，不直接调用 data source —
这正是真实数据与 mock 数据可以无感切换的原因。

## 绘图模块约定

`cedar_graph.plots.<region>.<name>.default` 下的每一个绘图
模块都对外暴露相同的四个符号：

```python
@dataclass
class PlotMetadata(BasePlotMetadata):
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    # 该图种自身的额外配置项，例如 area_range、level …

@dataclass
class PlotData:
    field_x: xr.DataArray
    # 其它已经准备好可以直接绘图的字段

def load_data(data_loader, start_time, forecast_time, **kwargs) -> PlotData: ...

def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel: ...
```

`load_data` 负责调取数据并完成必要的预处理；
`plot` 在此基础上构造 {class}`cedarkit.plots.chart.Panel`，
画底图、风羽、等值线，设置标题与色标，最后返回 Panel。

## quick_plot

{func}`cedar_graph.quickplot.quick_plot` 是面向 CMA-HPC 交互式
使用的便捷入口。给定图种名称（例如 `"cn.t_2m.default"`）、
业务系统名以及预报时间参数，它会自动选择对应的绘图模块、
创建 `LocalDataSource`、依次调用 `load_data` 与 `plot`。
入参支持字符串形式的时间（如 `"2025081900"`）和时间间隔
（如 `"24h"`）。
