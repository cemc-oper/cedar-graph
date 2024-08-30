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

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import apcp_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    interval: pd.Timedelta = pd.Timedelta(hours=24),
    system_name: str = None
    area_name: Optional[str] = None
    area_range: Optional[AreaRange] = None


@dataclass
class PlotData:
    field_rain: xr.DataArray


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        interval: pd.Timedelta = pd.Timedelta(hours=24),
        **kwargs
) -> PlotData:
    plot_logger.debug("loading apcp for current forecast time...")
    field_apcp = data_loader.load(
        apcp_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    previous_forecast_time = forecast_time - interval
    plot_logger.debug("loading apcp for current previous time...")
    previous_field_apcp = data_loader.load(
        apcp_info,
        start_time=start_time,
        forecast_time=previous_forecast_time,
    )

    # raw data -> plot data
    plot_logger.debug("calculating...")
    total_field_rain = field_apcp - previous_field_apcp

    plot_logger.debug("loading done")

    return PlotData(
        field_rain=total_field_rain,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range

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

    # create domain
    if area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=area_range)
    previous_forecast_time = forecast_time - pd.Timedelta(hours=24)
    forcast_hour_label = f"{int(forecast_time/pd.Timedelta(hours=1)):03d}"
    previous_forcast_hour_label = f"{int(previous_forecast_time/pd.Timedelta(hours=1)):03d}"
    graph_name = f"surface cumulated precipitation: {previous_forcast_hour_label}-{forcast_hour_label}h"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_rain = plot_data.field_rain

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_rain, style=rain_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=rain_style)
    plot_logger.debug("plotting...done")

    return panel
