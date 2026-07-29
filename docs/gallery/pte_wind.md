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

# 假相当位温差 + 风场（`cn.pte_wind`）

```{code-cell} python
import pandas as pd

from cedar_graph.data import DataLoader
from cedar_graph.testing import MockDataSource
from cedar_graph.plots.cn.pte_wind.default import PlotMetadata, load_data, plot

start_time = pd.Timestamp("2024-07-01 00:00:00")
forecast_time = pd.Timedelta(hours=24)
wind_level = 850.0
pte_levels = (500, 850)

data_loader = DataLoader(data_source=MockDataSource())
plot_data = load_data(
    data_loader=data_loader,
    start_time=start_time,
    forecast_time=forecast_time,
    wind_level=wind_level,
    pte_levels=pte_levels,
)
metadata = PlotMetadata(
    start_time=start_time,
    forecast_time=forecast_time,
    system_name="CMA-GFS",
    wind_level=wind_level,
    pte_levels=pte_levels,
    sample_step=0.5,
)
panel = plot(plot_data=plot_data, plot_metadata=metadata)
panel.show()
```
