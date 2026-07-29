---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# 手动绘图

`quick_plot` 用起来方便，但中间过程不可见。当你需要查看中间
数据、切换数据源或在一张图里组合多个面板时，建议直接驱动
绘图模块。

下面这个例子用 {class}`cedar_graph.testing.MockDataSource` 绘制
500 hPa 高度场与海平面气压，这样图就可以直接在文档构建过程中
渲染出来。如果要对接 CMA-HPC 真实数据，把数据源改成
{class}`cedar_graph.data.LocalDataSource(system_name="CMA-MESO")`
即可，其它代码不变。

```{code-cell} python
import pandas as pd

from cedar_graph.data import DataLoader
from cedar_graph.testing import MockDataSource
from cedar_graph.plots.cn.height_500_mslp.default import (
    PlotMetadata,
    load_data,
    plot,
)

start_time = pd.Timestamp("2024-07-01 00:00:00")
forecast_time = pd.Timedelta(hours=24)

# 业务系统 -> 数据字段
data_source = MockDataSource()
data_loader = DataLoader(data_source=data_source)
plot_data = load_data(
    data_loader=data_loader,
    start_time=start_time,
    forecast_time=forecast_time,
)

# 数据字段 -> 绘图
metadata = PlotMetadata(
    start_time=start_time,
    forecast_time=forecast_time,
    system_name="CMA-GFS",
    sample_step=0.5,
)
panel = plot(plot_data=plot_data, plot_metadata=metadata)

# 输出图像
panel.show()
```

`cedar_graph.plots.cn.*` 下的所有图种都遵循同样的模式。
图种特有的参数放在 `PlotMetadata`（例如 `area_range`、`level`、
`wind_level`、`interval`）上，或通过 `load_data` 的关键字参数传入。
完整的图集请见 {doc}`../gallery/index`。
