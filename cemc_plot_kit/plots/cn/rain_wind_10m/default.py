from dataclasses import dataclass
from copy import deepcopy
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.maps.style import ContourStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.colormap import generate_colormap_using_ncl_colors
from cedarkit.maps.util import AreaRange

from cemc_plot_kit.data import DataLoader
from cemc_plot_kit.data.field_info import apcp_info, u_info, v_info


@dataclass
class PlotData:
    rain_field: xr.DataArray
    u_field: xr.DataArray
    v_field: xr.DataArray


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp
    forecast_time: pd.Timedelta
    interval: pd.Timedelta
    system_name: str
    area_range: Optional[AreaRange] = None


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        interval: pd.Timedelta,
) -> PlotData:
    wind_level = 10
    wind_level_type = "heightAboveGround"

    u_10m_info = deepcopy(u_info)
    u_10m_info.level_type = wind_level_type
    u_10m_info.level = wind_level

    v_10m_info = deepcopy(v_info)
    v_10m_info.level_type = wind_level_type
    v_10m_info.level = wind_level

    apcp_field = data_loader.load(
        apcp_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    u_10m_field = data_loader.load(
        u_10m_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    v_10m_field = data_loader.load(
        v_10m_info,
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
        u_field=u_10m_field,
        v_field=v_10m_field,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    rain_field = plot_data.rain_field
    u_field = plot_data.u_field
    v_field = plot_data.v_field

    interval = plot_metadata.interval

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

    # plot
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)
    panel = Panel(domain=domain)
    panel.plot(rain_field, style=rain_style)

    previous_forecast_time = plot_metadata.forecast_time - interval
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
