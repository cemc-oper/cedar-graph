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
from cedar_graph.data.field_info import u_info, v_info, bpli_info
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
    wind_level: float = None


@dataclass
class PlotData:
    field_bpli: xr.DataArray
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
    plot_logger.debug("loading bpli...")
    field_bpli = data_loader.load(
        field_info=bpli_info,
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
        field_bpli=field_bpli,
        field_u=field_u,
        field_v=field_v,
        wind_level=wind_level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    wind_level = plot_metadata.wind_level
    area_range = plot_metadata.area_range
    area_name = plot_metadata.area_name

    bpli_levels = np.array([-48, -42, -36, -30, -24, -18, -12, -6, 0])
    colormap_index = np.array([20, 19, 18, 16, 14, 12, 10, 8, 6, 4]) - 2
    bpli_colormap = get_ncl_colormap("prcp_3", index=colormap_index)

    bpli_style = ContourStyle(
        colors=bpli_colormap,
        levels=bpli_levels,
        fill=True,
    )
    bpli_line_style = ContourStyle(
        colors="black",
        levels=bpli_levels,
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
        graph_name = f"BPLI(shadow) and {wind_level}hPa Wind(m/s)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} BPLI(shadow) and {wind_level}hPa Wind(m/s)"

    # prepare data
    plot_logger.debug(f"preparing data...")
    total_area = domain.total_area()
    plot_data = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_bpli = plot_data.field_bpli
    plot_field_u = plot_data.field_u
    plot_field_v = plot_data.field_v

    # create panel and plot
    plot_logger.debug(f"plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_bpli, style=bpli_style)
    panel.plot(plot_field_bpli, style=bpli_line_style)
    panel.plot([[plot_field_u, plot_field_v]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=bpli_style)
    plot_logger.debug(f"plotting...done")

    return panel
