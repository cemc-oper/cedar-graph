from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.maps.style import ContourStyle, ContourLabelStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import u_info, v_info, bli_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    """
    Information except data needed by plot.
    All properties are default None to create an empty instance.

    Attributes
    ----------
    start_time : pd.Timestamp
    forecast_time : pd.Timestamp
    system_name : str
        system name is printed in the top right corner of the plot box.
    area_range : Optional[AreaRange]
        plot area. If None, draw china.
    area_name : Optional[str]
        plot area name. Should be set when area_range is not None.
    wind_level : float
        level value for wind fields.
    """
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_range: Optional[AreaRange] = None
    area_name: Optional[str] = None
    wind_level: float = None


@dataclass
class PlotData:
    """
    All data needed by plot.

    Attributes
    ----------
    field_bli : xr.DataArray
        BLI field.
    field_u : xr.DataArray
        U field.
    field_v : xr.DataArray
        V field.
    wind_level : float
        level value for U and V fields.
    """
    field_bli: xr.DataArray
    field_u: xr.DataArray
    field_v: xr.DataArray
    wind_level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        wind_level: float,
        **kwargs,
) -> PlotData:
    """
    load data from data loader.

    Parameters
    ----------
    data_loader
        A data loader with some data source.
    start_time
    forecast_time
    wind_level
        level value for wind fields.
    kwargs

    Returns
    -------
    PlotData
        plot data
    """
    plot_logger.debug("loading bli...")
    field_bli = data_loader.load(
        field_info=bli_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug(f"loading u {wind_level}hPa...")
    u_level_info = deepcopy(u_info)
    u_level_info.level_type = "pl"
    u_level_info.level = wind_level
    field_u = data_loader.load(
        field_info=u_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.debug(f"loading v {wind_level}hPa...")
    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    field_v = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )
    plot_logger.debug(f"loading done")

    return PlotData(
        field_bli=field_bli,
        field_u=field_u,
        field_v=field_v,
        wind_level=wind_level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    """
    Plot the graph using plot data and plot metadata.

    Parameters
    ----------
    plot_data
        data for plot.
    plot_metadata
        metadata for plot.

    Returns
    -------
    Panel
        plot panel object.
    """
    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    wind_level = plot_metadata.wind_level
    area_range = plot_metadata.area_range
    area_name = plot_metadata.area_name

    bli_levels = np.array([-48, -42, -36, -30, -24, -18, -12, -6, 0])
    colormap_index = np.array([20, 19, 18, 16, 14, 12, 10, 8, 6, 4]) - 2
    bli_colormap = get_ncl_colormap("prcp_3", index=colormap_index)

    bli_style = ContourStyle(
        colors=bli_colormap,
        levels=bli_levels,
        fill=True,
    )
    bli_line_style = ContourStyle(
        colors="black",
        levels=bli_levels,
        linewidths=0.5,
        fill=False,
        label=True,
        label_style=ContourLabelStyle(
            fontsize=7,
            background_color="white"
        )
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
        graph_name = f"BLI(shadow) and {wind_level}hPa Wind(m/s)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} BLI(shadow) and {wind_level}hPa Wind(m/s)"

    # prepare data
    plot_logger.debug(f"preparing data...")
    total_area = domain.total_area()
    plot_data = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_bli = plot_data.field_bli
    plot_field_u = plot_data.field_u
    plot_field_v = plot_data.field_v

    # create panel and plot
    plot_logger.debug(f"plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_bli, style=bli_style)
    panel.plot(plot_field_bli, style=bli_line_style)
    panel.plot([[plot_field_u, plot_field_v]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=bli_style)
    plot_logger.debug(f"plotting...done")

    return panel
