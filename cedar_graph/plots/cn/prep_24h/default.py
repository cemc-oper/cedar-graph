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

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import apcp_info, asnow_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_range: Optional[AreaRange] = None
    area_name: str = None


@dataclass
class PlotData:
    field_rain: xr.DataArray
    field_rain_snow: xr.DataArray
    field_snow: xr.DataArray


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        interval: pd.Timedelta = pd.Timedelta(hours=24),
        **kwargs,
) -> PlotData:
    plot_logger.debug("loading apcp for current forecast time...")
    field_apcp = data_loader.load(
        apcp_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug("loading asnow for current forecast time...")
    field_asnow = data_loader.load(
        asnow_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    previous_forecast_time = forecast_time - interval

    plot_logger.debug("loading apcp for previous forecast time...")
    previous_field_apcp = data_loader.load(
        apcp_info,
        start_time=start_time,
        forecast_time=previous_forecast_time,
    )

    plot_logger.debug("loading asnow for previous forecast time...")
    previous_field_asnow = data_loader.load(
        asnow_info,
        start_time=start_time,
        forecast_time=previous_forecast_time,
    )

    # raw data -> plot data
    plot_logger.debug("calculating...")
    field_total_rain = field_apcp - previous_field_apcp
    field_total_snow = (field_asnow - previous_field_asnow) * 1000

    field_total_rain = xr.where(field_total_rain > 0, field_total_rain, np.nan)
    ratio = field_total_snow / field_total_rain

    field_rain = xr.where(ratio < 0.25, field_total_rain, np.nan)
    field_rain_snow = xr.where(np.logical_and(ratio >= 0.25, ratio <= 0.75), field_total_rain, np.nan)
    field_snow = xr.where(ratio > 0.75, field_total_rain, np.nan)

    plot_logger.debug("loading done")

    return PlotData(
        field_rain=field_rain,
        field_rain_snow=field_rain_snow,
        field_snow=field_snow,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range

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

    # create domain
    if area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=area_range)

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_rain = plot_data.field_rain
    plot_field_rain_snow = plot_data.field_rain_snow
    plot_field_snow = plot_data.field_snow

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_rain, style=rain_style)
    panel.plot(plot_field_snow, style=snow_style)
    panel.plot(plot_field_rain_snow, style=rain_snow_style)

    previous_forecast_time = forecast_time - pd.Timedelta(hours=24)
    forcast_hour_label = f"{int(forecast_time/pd.Timedelta(hours=1)):03d}"
    previous_forcast_hour_label = f"{int(previous_forecast_time/pd.Timedelta(hours=1)):03d}"
    domain.set_title(
        panel=panel,
        graph_name=f"surface cumulated precipitation: {previous_forcast_hour_label}-{forcast_hour_label}h",
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=[rain_style, rain_snow_style, snow_style])
    plot_logger.debug("plotting...done")

    return panel
