from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.maps.style import ContourStyle, ColorbarStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.colormap import generate_colormap_using_ncl_colors
from cedarkit.maps.util import AreaRange

from cemc_plot_kit.data import DataLoader
from cemc_plot_kit.data.field_info import apcp_info


@dataclass
class PlotData:
    rain_field: xr.DataArray


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp
    forecast_time: pd.Timedelta
    system_name: str
    area_range: Optional[AreaRange] = None


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        interval: pd.Timedelta = pd.Timedelta(hours=24),
) -> PlotData:
    apcp_field = data_loader.load(
        apcp_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    previous_forecast_time = forecast_time - interval

    previous_apcp_field = data_loader.load(
        apcp_info,
        start_time=start_time,
        forecast_time=previous_forecast_time,
    )

    # raw data -> plot data
    total_rain_field = apcp_field - previous_apcp_field

    return PlotData(
        rain_field=total_rain_field,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    rain_field = plot_data.rain_field

    # style
    # 24小时降水常用填充图样式
    rain_contour_lev = np.array([0.1, 10, 25, 50, 100, 200])
    rain_color_map = generate_colormap_using_ncl_colors(
        [
            "transparent",
            "White",
            "DarkOliveGreen3",
            "forestgreen",
            "deepSkyBlue",
			"Blue",
            "Magenta",
            "deeppink4"
        ],
        name="rain"
    )
    rain_style = ContourStyle(
        colors=rain_color_map,
        levels=rain_contour_lev,
        fill=True,
        colorbar_style=ColorbarStyle(label="rain")
    )

    # plot
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)
    panel = Panel(domain=domain)
    panel.plot(rain_field, style=rain_style)

    previous_forecast_time = plot_metadata.forecast_time - pd.Timedelta(hours=24)
    forcast_hour_label = f"{int(plot_metadata.forecast_time/pd.Timedelta(hours=1)):03d}"
    previous_forcast_hour_label = f"{int(previous_forecast_time/pd.Timedelta(hours=1)):03d}"
    domain.set_title(
        panel=panel,
        graph_name=f"surface cumulated precipitation: {previous_forcast_hour_label}-{forcast_hour_label}h",
        system_name=plot_metadata.system_name,
        start_time=plot_metadata.start_time,
        forecast_time=plot_metadata.forecast_time,
    )
    domain.add_colorbar(panel=panel, style=rain_style)

    return panel
