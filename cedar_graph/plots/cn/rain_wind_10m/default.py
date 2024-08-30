from dataclasses import dataclass
from copy import deepcopy
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.maps.style import ContourStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.colormap import generate_colormap_using_ncl_colors
from cedarkit.maps.util import AreaRange

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import apcp_info, u_info, v_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger= get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    interval: pd.Timedelta = None
    system_name: str = None
    area_name: Optional[str] = None
    area_range: Optional[AreaRange] = None


@dataclass
class PlotData:
    field_rain: xr.DataArray
    field_u: xr.DataArray
    field_v: xr.DataArray


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        interval: pd.Timedelta,
        **kwargs,
) -> PlotData:
    wind_level = 10
    wind_level_type = "heightAboveGround"

    u_10m_info = deepcopy(u_info)
    u_10m_info.level_type = wind_level_type
    u_10m_info.level = wind_level

    v_10m_info = deepcopy(v_info)
    v_10m_info.level_type = wind_level_type
    v_10m_info.level = wind_level

    plot_logger.debug("loading apcp for current forecast time...")
    field_apcp = data_loader.load(
        apcp_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug("loading u 10m...")
    field_u_10m = data_loader.load(
        u_10m_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    plot_logger.debug("loading v 10m...")
    field_v_10m = data_loader.load(
        v_10m_info,
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

    # raw data -> plot data
    plot_logger.debug("calculating...")
    total_field_rain = field_apcp - previous_field_apcp

    plot_logger.debug("loading done")

    return PlotData(
        field_rain=total_field_rain,
        field_u=field_u_10m,
        field_v=field_v_10m,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    start_time = plot_metadata.start_time
    interval = plot_metadata.interval
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name
    area_range = plot_metadata.area_range
    area_name = plot_metadata.area_name

    # style
    if interval == pd.Timedelta(hours=1):
        map_colors = [
            "White",
            "DarkOliveGreen1",
            "DarkOliveGreen3",
            "forestgreen",
            "deepSkyBlue",
            "Blue",
            "darkgreen",
            "Magenta",
            "darkorange",
            "deeppink4",
        ]
        rain_color_map = generate_colormap_using_ncl_colors(map_colors, "rain_1h_colormap")
        rain_level = np.array([0.1, 1, 2, 4, 6, 8, 10, 20, 50])
    elif interval == pd.Timedelta(hours=3):
        map_colors = [
            "White",
            "DarkOliveGreen3",
            "forestgreen",
            "deepSkyBlue",
            "Blue",
            "Magenta",
            "deeppink4"
        ]
        rain_color_map = generate_colormap_using_ncl_colors(map_colors, "rain_3h_colormap")
        rain_level = np.array([0.1, 3, 10, 20, 50, 70])
    elif interval == pd.Timedelta(hours=6):
        map_colors = [
            "White",
            "DarkOliveGreen3",
            "forestgreen",
            "deepSkyBlue",
            "Blue",
            "Magenta"
        ]
        rain_color_map = generate_colormap_using_ncl_colors(map_colors, "rain_6h_colormap")
        rain_level = np.array([0.1, 4, 13, 25, 60])
    elif interval == pd.Timedelta(hours=12):
        map_colors = [
            "White",
            "DarkOliveGreen3",
            "forestgreen",
            "deepSkyBlue",
            "Blue",
            "Magenta",
            "deeppink4",
        ]
        rain_color_map = generate_colormap_using_ncl_colors(map_colors, "rain_12h_colormap")
        rain_level = np.array([0.1, 5, 15, 30, 70, 140])
    elif interval == pd.Timedelta(hours=24):
        map_colors = [
                "transparent",
                "White",
                "DarkOliveGreen3",
                "forestgreen",
                "deepSkyBlue",
	    		"Blue",
                "Magenta",
                "deeppink4",
            ]
        rain_color_map = generate_colormap_using_ncl_colors(map_colors, name="rain_24h_colormap")
        rain_level = np.array([0.1, 10, 25, 50, 100, 200])
    else:
        raise ValueError(f"forecast interval is not supported: {interval}")

    rain_style = ContourStyle(
        colors=rain_color_map,
        levels=rain_level,
        fill=True,
    )

    barb_style = BarbStyle(
        barbcolor="black",
        flagcolor="black",
        linewidth=0.3,
        # barb_increments=dict(half=2, full=4, flag=20)
    )

    # create domain
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=area_range)
    previous_forecast_time = forecast_time - interval
    forcast_hour_label = f"{int(forecast_time/pd.Timedelta(hours=1)):03d}"
    previous_forcast_hour_label = f"{int(previous_forecast_time/pd.Timedelta(hours=1)):03d}"
    graph_name = f"surface cumulated precipitation: {previous_forcast_hour_label}-{forcast_hour_label}h"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_rain = plot_data.field_rain
    plot_field_u = plot_data.field_u
    plot_field_v = plot_data.field_v

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_rain, style=rain_style)
    panel.plot([[plot_field_u, plot_field_v]], style=barb_style, layer=[0])

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
