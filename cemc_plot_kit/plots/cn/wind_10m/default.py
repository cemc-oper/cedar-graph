from dataclasses import dataclass
from typing import Optional

import xarray as xr
import pandas as pd
import numpy as np

import matplotlib.colors as mcolors

from cedarkit.maps.style import ContourStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.util import AreaRange


@dataclass
class PlotData:
    u_10m_field: xr.DataArray
    v_10m_field: xr.DataArray
    wind_speed_10m_field: xr.DataArray


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp
    forecast_time: pd.Timedelta
    system_name: str
    area_range: Optional[AreaRange] = None


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    u_10m_field = plot_data.u_10m_field
    v_10m_field = plot_data.v_10m_field
    wind_speed_10m_field = plot_data.wind_speed_10m_field

    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name

    # style
    map_colors = np.array([
        (255, 255, 255),
        (0, 0, 0),
        (255, 255, 255),
        (0, 200, 200),
        (0, 210, 140),
        (0, 220, 0),
        (160, 230, 50),
        (230, 220, 50),
        (230, 175, 45),
        (240, 130, 40),
        (250, 60, 60),
        (240, 0, 130),
        (0, 0, 255),
        (255, 140, 0),
        (238, 18, 137)
    ], dtype=float) / 255
    colormap = mcolors.ListedColormap(map_colors)

    wind_speed_colormap = mcolors.ListedColormap(colormap(np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11])))
    wind_speed_contour_lev = np.array([3.4, 5.5, 8, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5])
    wind_speed_style = ContourStyle(
        colors=wind_speed_colormap,
        levels=wind_speed_contour_lev,
        fill=True,
    )

    barb_style = BarbStyle(
        barbcolor="black",
        flagcolor="black",
        linewidth=0.3,
        # barb_increments=dict(half=2, full=4, flag=20)
    )

    # plot
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)
    panel = Panel(domain=domain)
    panel.plot(wind_speed_10m_field, style=wind_speed_style)
    panel.plot([[u_10m_field[::50, ::50], v_10m_field[::50, ::50]]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name="10m Wind, 10m Wind Speed(m/s, shadow)",
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=wind_speed_style)

    return panel
