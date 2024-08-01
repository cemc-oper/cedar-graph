from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.maps.style import ContourStyle, ColorbarStyle
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.colormap import generate_colormap_using_ncl_colors
from cedarkit.maps.util import AreaRange

from cemc_plot_kit.data import DataLoader
from cemc_plot_kit.data.field_info import apcp_info, asnow_info


@dataclass
class PlotData:
    rain_field: xr.DataArray
    rain_snow_field: xr.DataArray
    snow_field: xr.DataArray


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
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

    asnow_field = data_loader.load(
        asnow_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    previous_forecast_time = forecast_time - interval

    previous_apcp_field = data_loader.load(
        apcp_info,
        start_time=start_time,
        forecast_time=previous_forecast_time,
    )

    previous_asnow_field = data_loader.load(
        asnow_info,
        start_time=start_time,
        forecast_time=previous_forecast_time,
    )

    # raw data -> plot data
    total_rain_field = apcp_field - previous_apcp_field
    total_snow_field = (asnow_field - previous_asnow_field) * 1000

    total_rain_field = xr.where(total_rain_field > 0, total_rain_field, np.nan)
    ratio = total_snow_field / total_rain_field

    rain_field = xr.where(ratio < 0.25, total_rain_field, np.nan)
    rain_snow_field = xr.where(np.logical_and(ratio >= 0.25, ratio <= 0.75), total_rain_field, np.nan)
    snow_field = xr.where(ratio > 0.75, total_rain_field, np.nan)

    return PlotData(
        rain_field=rain_field,
        rain_snow_field=rain_snow_field,
        snow_field=snow_field,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    rain_field = plot_data.rain_field
    rain_snow_field = plot_data.rain_snow_field
    snow_field = plot_data.snow_field

    # style
    # 24小时降水常用填充图样式
    rain_contour_lev = np.array([0.1, 10, 25, 50, 100, 250])
    rain_color_map = generate_colormap_using_ncl_colors(
        [
            "transparent",
            "PaleGreen2",
            "ForestGreen",
            "DeepSkyBlue",
            "blue1",
            "magenta1",
            "DeepPink3",
            "DarkOrchid4"
        ],
        name="rain"
    )
    rain_style = ContourStyle(
        colors=rain_color_map,
        levels=rain_contour_lev,
        fill=True,
        colorbar_style=ColorbarStyle(label="rain")
    )

    snow_contour_lev = np.array([0.1, 2.5, 5, 10, 20, 30])
    snow_color_map = get_ncl_colormap("mch_default", index=np.array([0, 7, 6, 5, 4, 3, 1]))
    snow_style = ContourStyle(
        colors=snow_color_map,
        levels=snow_contour_lev,
        fill=True,
        colorbar_style=ColorbarStyle(label="snow")
    )

    rain_snow_contour_lev = np.array([0.1, 10, 25, 50, 100])
    rain_snow_color_map = get_ncl_colormap("precip_diff_12lev", index=np.array([6, 5, 4, 3, 2, 1]))
    rain_snow_style = ContourStyle(
        colors=rain_snow_color_map,
        levels=rain_snow_contour_lev,
        fill=True,
        colorbar_style=ColorbarStyle(label="mix")
    )

    # plot
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)
    panel = Panel(domain=domain)
    panel.plot(rain_field, style=rain_style)
    panel.plot(snow_field, style=snow_style)
    panel.plot(rain_snow_field, style=rain_snow_style)

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
    domain.add_colorbar(panel=panel, style=[rain_style, rain_snow_style, snow_style])

    return panel
