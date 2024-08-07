from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.colors as mcolors

from cedarkit.maps.style import ContourStyle, ContourLabelStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cedarkit.comp.smooth import smth9
from cedarkit.comp.util import apply_to_xarray_values

from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import t_info, dew_t_info
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata:
    system_name: str = None
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    area_name: str = None
    area_range: AreaRange = None
    level: float = None


@dataclass
class PlotData:
    t_field: xr.DataArray
    t_dew_t_diff_field: xr.DataArray
    level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        level: float,
        **kwargs
) -> PlotData:
    plot_logger.info(f"loading t {level}hPa...")
    t_level_info = deepcopy(t_info)
    t_level_info.level_type = "pl"
    t_level_info.level = level
    t_field = data_loader.load(
        field_info=t_level_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.info(f"loading dpt {level}hPa...")
    dew_t_level_info = deepcopy(dew_t_info)
    dew_t_level_info.level_type = "pl"
    dew_t_level_info.level = level
    dew_t_field = data_loader.load(
        field_info=dew_t_level_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.info("calculating...")
    t_dew_t_diff_field = t_field - dew_t_field
    t_dew_t_diff_field = apply_to_xarray_values(t_dew_t_diff_field, lambda x: smth9(x, 0.5, 0.25, True))
    t_dew_t_diff_field = apply_to_xarray_values(t_dew_t_diff_field, lambda x: smth9(x, 0.5, 0.25, True))

    t_field = t_field - 273.15
    t_field = apply_to_xarray_values(t_field, lambda x: smth9(x, 0.5, 0.25, True))
    t_field = apply_to_xarray_values(t_field, lambda x: smth9(x, 0.5, 0.25, True))

    return PlotData(
        t_field=t_field,
        t_dew_t_diff_field=t_dew_t_diff_field,
        level=level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata):
    t_field = plot_data.t_field
    t_dew_t_diff_field = plot_data.t_dew_t_diff_field

    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
    if area_name is None:
        area_name = ""
    area_range = plot_metadata.area_range
    level = plot_metadata.level

    # 合并色表
    map_colors = np.array([
        (255, 0, 255),
        (77, 77, 77)
    ], dtype=float) / 255.0
    ncl_color_map = get_ncl_colormap("testcmap")
    ncl_colors = ncl_color_map.colors
    colors = np.concatenate((ncl_colors, map_colors), axis=0)
    color_map = mcolors.ListedColormap(colors, "plot_colormap")

    t_dew_t_diff_levels = np.array([1, 3, 5, 7, 9, 11, 15, 17, 21, 25, 29, 33])

    color_index = np.array([65, 70, 75, 80, 85, 100, 115, 130, 150, 160, 170, 180, 190]) - 2
    t_dew_t_diff_colormap = mcolors.ListedColormap(color_map(color_index), "t_dew_t_diff_colormap")

    t_dew_t_diff_style = ContourStyle(
        colors=t_dew_t_diff_colormap,
        levels=t_dew_t_diff_levels,
        fill=True,
    )

    line_color_index = np.array([65, 70, 201, 80, 85, 100, 115, 130, 150, 160, 170, 180, 190]) - 2
    t_dew_t_diff_line_colors = mcolors.ListedColormap(color_map(line_color_index), "t_dew_t_diff_line_colormap")
    t_dev_t_diff_line_widths = np.array([0.1, 0.1, 2.0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
    t_dew_t_diff_line_style = ContourStyle(
        levels=t_dew_t_diff_levels,
        colors=t_dew_t_diff_line_colors,
        linewidths=t_dev_t_diff_line_widths,
    )

    t_levels = np.linspace(start=-80, stop=80, num=81, endpoint=True)
    t_line_widths = np.where(t_levels == 0, 2.0, 1.0)
    t_line_colors = []
    t_lines_color = color_map(30 - 2)
    for current_level in t_levels:
        if current_level == 0:
            t_line_colors.append((0, 0, 0, 0))  # black
        else:
            t_line_colors.append(t_lines_color)

    t_line_style = ContourStyle(
        colors=t_line_colors,
        levels=t_levels,
        linewidths=t_line_widths,
        linestyles="solid",
        fill=False,
        label=True,
        label_style=ContourLabelStyle(
            colors=t_line_colors,
            background_color="white",
        )
    )

    # plot
    if area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)
    panel = Panel(domain=domain)
    panel.plot(t_dew_t_diff_field[::2, ::2], style=t_dew_t_diff_style)
    panel.plot(t_dew_t_diff_field[::2, ::2], style=t_dew_t_diff_line_style)
    panel.plot(t_field[::2, ::2], style=t_line_style)

    domain.set_title(
        panel=panel,
        graph_name=fr"{area_name} {level}hPa Temperature($^\circ$C) and Dew Temperature Diff.($^\circ$C,shadow)",
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=t_dew_t_diff_style)

    return panel
