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
图种定义（配方或 Python 绘图模块）。

{func}`~cedarkit.plots.engine.loader.get_plot_definition`
按 `plot_type` 先查配方、再查 Python 模块，返回的对象统一暴露
`PlotMetadata` / `load_data` / `plot` 三件套接口。下面这个例子用
{class}`cedar_graph.testing.MockDataSource` 绘制
500 hPa 高度场与海平面气压（配方 `cn.h_500_psl`），这样图就可以
直接在文档构建过程中渲染出来。如果要对接 CMA-HPC 真实数据，
把数据源改成
`cedar_graph.data.LocalDataSource(system_name="CMA-MESO")`
即可，其它代码不变。

```{code-cell} python
import pandas as pd

from cedar_graph.recipes.engine import get_recipe_engine
from cedar_graph.testing import build_mock_data_loader
from cedarkit.plots.engine.loader import get_plot_definition

start_time = pd.Timestamp("2024-07-01 00:00:00")
forecast_time = pd.Timedelta(hours=24)

# 图种定义：先配方（recipes/cn/h_500_psl.yaml）后模块
plot_module = get_plot_definition(
    plot_type="cn.h_500_psl",
    base_module_name="cedar_graph.plots",
    recipe_base_module="cedar_graph.recipes",
    engine=get_recipe_engine(),
)

# 业务系统 -> 数据字段
data_loader = build_mock_data_loader()
plot_data = plot_module.load_data(
    data_loader=data_loader,
    start_time=start_time,
    forecast_time=forecast_time,
)

# 数据字段 -> 绘图
metadata = plot_module.PlotMetadata(
    start_time=start_time,
    forecast_time=forecast_time,
    system_name="CMA-GFS",
    sample_step=0.5,
)
panel = plot_module.plot(plot_data=plot_data, plot_metadata=metadata)

# 输出图像
panel.show()
```

所有图种都遵循同样的模式——配方（`cn.t2m`、`cn.h_500_psl` …）
与 Python 逃生舱模块（`cn.shr.default` 等）只是加载来源不同。
图种特有的参数放在 `PlotMetadata`（例如 `area_range`、
`wind_level`、`interval`）上，同时传入 `load_data` 的关键字参数。
完整的图集请见 {doc}`../gallery/index`；新增自己的配方请见
{doc}`recipe`。
