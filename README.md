# cedar-graph

使用 cedarkit-maps 开发的绘图示例包。

## 快速绘图

绘制 2 米温度填充图

```py
from cedar_graph.quickplot import quick_plot

plot_type = "cn.t_2m.default"
plot_settings = dict(
    system_name="CMA-GFS",
    start_time="2024073000",
    forecast_time="48h",
)

quick_plot(
    plot_type=plot_type,
    **plot_settings,
)
```

绘制区域 10 米风场填充图

```py
from cedar_graph.quickplot import quick_plot
from cedarkit.maps.util import AreaRange

plot_type = "cn.wind_10m.default"
plot_settings = dict(
    system_name="CMA-MESO",
    start_time="2024073000",
    forecast_time="48h",
    area_name="NorthEast",
    area_range=AreaRange.from_tuple((108, 137, 37, 55))
)

quick_plot(
    plot_type=plot_type,
    **plot_settings,
)
```

## 绘图模块

使用绘图模块的函数和类实现图形绘制

```py
import pandas as pd

from cedar_graph.plots.cn.t_2m.default import PlotMetadata, plot, load_data
from cedar_graph.data import LocalDataSource, DataLoader

system_name = "CMA-MESO"
start_time = pd.to_datetime("2024-07-17 00:00:00")
forecast_time = pd.to_timedelta("24h")

metadata = PlotMetadata(
    start_time=start_time,
    forecast_time=forecast_time,
    system_name=system_name
)

# system -> field
data_source = LocalDataSource(system_name=system_name)
data_loader = DataLoader(data_source=data_source)
plot_data = load_data(
    data_loader=data_loader, 
    start_time=start_time, 
    forecast_time=forecast_time
)
    
# field -> plot
panel = plot(
    plot_data=plot_data,
    plot_metadata=metadata,
)

# plot -> output
panel.show()
```

## 绘图清单

| 类别 | 名称                  | 说明                        |
|----|---------------------|---------------------------|
| 常规 |                     |                           |
|    | height_500_mslp     | 500hPa高度场+海平面气压           |
|    | height_500_wind_850 | 500hPa高度场+850hPa风场        |
|    | t_2m                | 2米温度                      |
|    | wind_10m            | 10米风场                     |
| 诊断 |                     |                           |
|    | radar_reflectivity  | 雷达组合反射率                   |
|    | div_wind            | 散度+风场                     |
|    | k_wind              | K指数+风场                    |
|    | cin_wind            | CIN+风场                    |
|    | cape_wind           | CAPE+风场                   |
|    | bpli_wind           | 最优抬升指数+风场                 |
|    | pte_wind            | 500hPa与850hPa假相当位温之差+风场   |
|    | qv_div              | 水汽通量散度                    |
|    | shr                 | 垂直风切变 (0-1km/0-3km/0-6km) |
|    | t_dew_t             | 温度和露点差                    |
| 降水 |                     |                           |
|    | prep_24h            | 24小时降水 (多相态)              |
|    | rain_24h            | 24小时降水                    |
|    | rain_wind_10m       | 1/3/6/12/24小时降水+10米风场     |


## LICENSE

Copyright &copy; 2024, developers at cemc-oper.

`cedar-graph` is licensed under [Apache License V2.0](./LICENSE)
