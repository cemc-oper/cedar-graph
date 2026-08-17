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

# CAPE + 风场（`cn.cape_wind`）

本图由配方 `cedar_graph/recipes/cn/cape_wind.yaml` 驱动——
风场层次由必需参数 `wind_level` 指定。

```{code-cell} python
import pandas as pd

from cedar_graph.recipes.engine import get_recipe_engine
from cedar_graph.testing import build_mock_data_loader
from cedarkit.plots.engine.loader import get_plot_definition

start_time = pd.Timestamp("2024-07-01 00:00:00")
forecast_time = pd.Timedelta(hours=24)

plot_module = get_plot_definition(
    plot_type="cn.cape_wind",
    base_module_name="cedar_graph.plots",
    recipe_base_module="cedar_graph.recipes",
    engine=get_recipe_engine(),
)

data_loader = build_mock_data_loader()
plot_data = plot_module.load_data(
    data_loader=data_loader,
    start_time=start_time,
    forecast_time=forecast_time,
    wind_level=850.0,
)
metadata = plot_module.PlotMetadata(
    start_time=start_time,
    forecast_time=forecast_time,
    system_name="CMA-GFS",
    sample_step=0.5,
    wind_level=850.0,
)
panel = plot_module.plot(plot_data=plot_data, plot_metadata=metadata)
panel.show()
```
