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

from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import u_info, v_info, bpli_info
from cedar_graph.data.operator import extract_area, sample_nearest
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_range: Optional[AreaRange] = None
    area_name: str = None
    wind_level: float = None


@dataclass
class PlotData:
    bpli_field: xr.DataArray
    u_field: xr.DataArray
    v_field: xr.DataArray
    wind_level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        wind_level: float,
        **kwargs,
) -> PlotData:
    plot_logger.debug("loading bpli...")
    bpli_field = data_loader.load(
        field_info=bpli_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug(f"loading u {wind_level}hPa...")
    u_level_info = deepcopy(u_info)
    u_level_info.level_type = "pl"
    u_level_info.level = wind_level
    u_field = data_loader.load(
        field_info=u_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.debug(f"loading v {wind_level}hPa...")
    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    v_field = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    return PlotData(
        bpli_field=bpli_field,
        u_field=u_field,
        v_field=v_field,
        wind_level=wind_level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    bpli_field = plot_data.bpli_field
    u_field = plot_data.u_field
    v_field = plot_data.v_field

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

    # plot
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
        graph_name = f"BPLI(shadow) and {wind_level}hPa Wind(m/s)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} BPLI(shadow) and {wind_level}hPa Wind(m/s)"

    panel = Panel(domain=domain)

    plot_bpli_field = bpli_field
    plot_u_field = u_field
    plot_v_field = v_field

    auto_extract = True
    if auto_extract:
        total_area = domain.total_area()
        plot_bpli_field = extract_area(bpli_field, area=total_area)
        plot_u_field = extract_area(u_field, area=total_area)
        plot_v_field = extract_area(v_field, area=total_area)

    auto_sample = True
    if auto_sample:
        longitude_step = 0.09
        plot_bpli_field = sample_nearest(plot_bpli_field, longitude_step=longitude_step)
        plot_u_field = sample_nearest(plot_u_field, longitude_step=longitude_step)
        plot_v_field = sample_nearest(plot_v_field, longitude_step=longitude_step)

    panel.plot(plot_bpli_field, style=bpli_style)
    panel.plot(plot_bpli_field, style=bpli_line_style)
    panel.plot([[plot_u_field, plot_v_field]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=bpli_style)

    return panel
