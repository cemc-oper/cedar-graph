from dataclasses import dataclass
from typing import Optional

import xarray as xr
import pandas as pd
import numpy as np

import matplotlib.colors as mcolors

from cedarkit.maps.style import ContourStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cemc_plot_kit.data import DataLoader
from cemc_plot_kit.data.field_info import t_2m_info


@dataclass
class PlotData:
    t_2m_field: xr.DataArray


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_range: Optional[AreaRange] = None


def load_data(data_loader: DataLoader, start_time: pd.Timestamp, forecast_time: pd.Timedelta) -> PlotData:
    # data file -> data field
    t_2m_field = data_loader.load(
        field_info=t_2m_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    # data field -> plot data
    t_2m_field = t_2m_field - 273.15

    return PlotData(
        t_2m_field=t_2m_field
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    """
    绘制2米温度图形

    Parameters
    ----------
    plot_data
        绘图数据，已经过预处理，直接用来绘图
    plot_metadata
        绘图元信息，包括时间、系统名（、绘图区域）等

    Returns
    -------
    Panel
        cedarkit.maps 包的绘图板对象
    """
    t_2m_field = plot_data.t_2m_field

    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name

    # style
    color_map = get_ncl_colormap("BlAqGrYeOrReVi200")

    month = start_time.month
    if 5 <= month <= 9:
        t_2m_level = [-12, -8, -4, 0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44]
        color_index = np.array([2, 18, 34, 50, 66, 82, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]) - 2
    else:
        t_2m_level = [-24, -20, -16, -12, -8, -4, 0, 4, 8, 12, 16, 20, 24, 28, 32]
        color_index = np.array([2, 12, 22, 32, 42, 52, 62, 72, 82, 92, 102, 112, 122, 132, 142, 152]) - 2

    t_2m_color_map = mcolors.ListedColormap(color_map(color_index))
    t_2m_style = ContourStyle(
        colors=t_2m_color_map,
        levels=t_2m_level,
        fill=True,
    )

    # plot
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)
    panel = Panel(domain=domain)
    panel.plot(t_2m_field, style=t_2m_style)

    domain.set_title(
        panel=panel,
        graph_name="2m Temperature (C)",
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=t_2m_style)

    return panel
