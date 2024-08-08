from dataclasses import dataclass
from typing import Optional, Dict
from copy import deepcopy

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.colors as mcolors

from cedarkit.maps.style import ContourStyle, ContourLabelStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import u_info, v_info, pte_info
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata:
    system_name: str = None
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    area_name: str = None
    area_range: AreaRange = None
    wind_level: float = None
    pte_levels: tuple[float, float] = (500, 850)


@dataclass
class PlotData:
    pte_field: xr.DataArray
    u_field: xr.DataArray
    v_field: xr.DataArray
    wind_level: float
    pte_levels: tuple[float, float] = (500, 850)


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        wind_level: float,
        pte_levels: tuple[float, float],
        **kwargs,
) -> PlotData:
    first_pte_level = pte_levels[0]
    second_pte_level = pte_levels[1]

    plot_logger.debug(f"loading pte {first_pte_level}hPa...")
    first_pte_info = deepcopy(pte_info)
    first_pte_info.level_type = "pl"
    first_pte_info.level = first_pte_level
    first_pte_field = data_loader.load(
        field_info=first_pte_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug(f"loading pte {second_pte_level}hPa...")
    second_pte_info = deepcopy(pte_info)
    second_pte_info.level_type = "pl"
    second_pte_info.level = second_pte_level
    second_pte_field = data_loader.load(
        field_info=second_pte_info,
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
        forecast_time=forecast_time,
    )

    plot_logger.debug(f"loading u {wind_level}hPa...")
    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    v_field = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug("calculating...")
    pte_field = first_pte_field - second_pte_field

    return PlotData(
        pte_field=pte_field,
        u_field=u_field,
        v_field=v_field,
        wind_level=wind_level,
        pte_levels=pte_levels,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    pte_field = plot_data.pte_field
    u_field = plot_data.u_field
    v_field = plot_data.v_field

    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range
    wind_level = plot_metadata.wind_level
    pte_levels = plot_data.pte_levels

    # 合并色表
    color_index = np.array([175, 160, 156, 140, 125, 110, 100, 90, 80, 60]) - 2
    ncl_color_map = get_ncl_colormap("BkBlAqGrYeOrReViWh200", index=color_index)
    ncl_colors = ncl_color_map.colors
    ncl_colors.append([1, 1, 1, 1])
    color_map = mcolors.ListedColormap(ncl_colors, "plot_colormap")

    pte_diff_level = np.array([-40, -35, -30, -25, -20, -15, -10, -5, 0, 5])
    pte_diff_style = ContourStyle(
        colors=color_map,
        levels=pte_diff_level,
        fill=True,
    )
    pte_diff_line_style = ContourStyle(
        colors="black",
        levels=pte_diff_level,
        fill=False,
        linestyles="solid",
        linewidths=0.6,
        label=True,
        label_style=ContourLabelStyle(
            colors="black",
            background_color="white",
            fontsize=8,
        )
    )

    barb_style = BarbStyle(
        barbcolor="black",
        flagcolor="black",
        linewidth=0.3,
        # barb_increments=dict(half=2, full=4, flag=20)
    )

    # plot
    if area_range is None:
        domain = EastAsiaMapTemplate()
        graph_name = f"PTE {pte_levels[0]}hPa-{pte_levels[1]}hPa(K,shadow) and {wind_level}hPa Wind(m/s)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} PTE {pte_levels[0]}hPa-{pte_levels[1]}hPa(K,shadow) and {wind_level}hPa Wind(m/s)"

    panel = Panel(domain=domain)
    panel.plot(pte_field[::2, ::2], style=pte_diff_style)
    panel.plot(pte_field[::2, ::2], style=pte_diff_line_style)
    panel.plot([[u_field[::2, ::2], v_field[::2, ::2]]], style=barb_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=pte_diff_style)

    return panel
