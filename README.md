# cedar-graph

![GitHub Release](https://img.shields.io/github/v/release/cemc-oper/cedar-graph)
![PyPI - Version](https://img.shields.io/pypi/v/cedar-graph)
![GitHub License](https://img.shields.io/github/license/cemc-oper/cedar-graph)
![GitHub Action Workflow Status](https://github.com/cemc-oper/cedar-graph/actions/workflows/ci.yaml/badge.svg)

A plotting example package using [cedarkit-maps](https://github.com/cemc-oper/cedarkit-maps).

## Install

Install using pip.

```bash
pip install cedar-graph
```

Or download the latest source code from GitHub repo and install the latest version.

## Quick plot

`quick_plot` can be used in CMA-HPC to draw and show picture using data from CEMC's NWP systems.

Draw contour fill plot for 2m temperature using CMA-GFS GRIB2 data.

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

Draw wind speed contour fill plot for 10m wind using CMA-MESO GRIB2 data.

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

## Manual plot

Use functions and classed in plotting modules to draw plots.

The following example runs at CMA-HPC.
First, create a `LocalDataSource` object to get data file path from CMA-MESO at CMA-HPC.
Next, use `load_data` and `plot` functions from `cedar_graph.plots.t_2m.default` module to draw a plot.
Finally, use `panel.show()` method to display the result.

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

## Graph list

| Category  | Plot Type           | Introduction                                                                           | 说明                        |
|-----------|---------------------|----------------------------------------------------------------------------------------|---------------------------|
| Normal    |                     |                                                                                        |                           |
|           | height_500_mslp     | 500hPa geopotential height + Sea level pressure                                        | 500hPa高度场+海平面气压           |
|           | height_500_wind_850 | 500hPa geopotential height + 850hPa wind                                               | 500hPa高度场+850hPa风场        |
|           | t_2m                | 2m temperature                                                                         | 2米温度                      |
|           | rh_2m               | 2m relative humidity                                                                   | 2米相对湿度                    |
|           | wind_10m            | 10m wind                                                                               | 10米风场                     |
| Diagnosis |                     |                                                                                        |                           |
|           | radar_reflectivity  | Composite radar reflectivity                                                           | 雷达组合反射率                   |
|           | div_wind            | Divergence + Wind                                                                      | 散度+风场                     |
|           | k_wind              | K Index + Wind                                                                         | K指数+风场                    |
|           | cin_wind            | CIN + Wind                                                                             | CIN+风场                    |
|           | cape_wind           | CAPE + Wind                                                                            | CAPE+风场                   |
|           | bli_wind            | Best lifted index + Wind                                                               | 最优抬升指数 + Wind             |
|           | pte_wind            | Difference in pseudo-equivalent potential temperature between 500hPa and 850hPa + Wind | 500hPa与850hPa假相当位温之差+风场   |
|           | qv_div              | Moisture flux divergence                                                               | 水汽通量散度                    |
|           | shr                 | Vertical wind shear (0-1km/0-3km/0-6km)                                                | 垂直风切变 (0-1km/0-3km/0-6km) |
|           | t_dew_t             | Temperature-dew point difference                                                       | 温度和露点差                    |
| Rain      |                     |                                                                                        |                           |
|           | prep_24h            | 24h precipitation (precipitation phase)                                                | 24小时降水 (多相态)              |
|           | rain_24h            | 24h rain                                                                               | 24小时降水                    |
|           | rain_wind_10m       | 1/3/6/12/24h rain + 10m wind                                                           | 1/3/6/12/24小时降水+10米风场     |


## LICENSE

Copyright &copy; 2024, developers at cemc-oper.

`cedar-graph` is licensed under [Apache License V2.0](./LICENSE)
