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

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import rh_2m_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_name: Optional[str] = None
    area_range: Optional[AreaRange] = None


@dataclass
class PlotData:
    field_rh_2m: xr.DataArray


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        **kwargs
) -> PlotData:
    # data file -> data field
    plot_logger.debug("loading t 2m...")
    rh_2m_field = data_loader.load(
        field_info=rh_2m_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    # data field -> plot data

    plot_logger.debug("loading done")

    return PlotData(
        field_rh_2m=rh_2m_field
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    """
    绘制2米湿度图形

    Parameters
    ----------
    plot_data
        绘图数据，已经过预处理，直接用来绘图
    plot_metadata
        绘图元信息，包括时间、系统名（、绘图区域）等

    Returns
    -------
    Panel
        绘图板对象
    """
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name
    area_range = plot_metadata.area_range

    # style
    color_map = get_ncl_colormap("rainbow+white+gray")

    rh_2m_level = np.linspace(70, 100, 7, endpoint=True)
    color_index = np.arange(90, 236, 20)

    # NOTE: NCL code for colormap
    # cmap=ispan(90,236,20)
    # cmap(0)=-1

    # color_index[0] = -1 # 透明
    color_index[0] = 236 # white

    rh_2m_color_map = mcolors.ListedColormap(color_map(color_index))
    rh_2m_style = ContourStyle(
        colors=rh_2m_color_map,
        levels=rh_2m_level,
        fill=True,
    )

    # create domain
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=area_range)
    graph_name = "2m Relative Humidity(%)"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_rh_2m = plot_data.field_rh_2m

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_rh_2m, style=rh_2m_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=rh_2m_style)
    plot_logger.debug("plotting...done")

    return panel
