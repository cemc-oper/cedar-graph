from dataclasses import dataclass
from typing import Literal, Optional
from copy import deepcopy

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.colors as mcolors

from cedarkit.plots.style import get_default_registry
from cedarkit.plots.chart import Panel
from cedarkit.plots.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.plots.calculate import calculate_levels_automatic
from cedarkit.plots.types import AreaRange

from cedarkit.comp.smooth import smth9
from cedarkit.comp.util import apply_to_xarray_values

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import vwsh_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    system_name: str = None
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    area_range: Optional[AreaRange] = None
    area_name: str = None
    first_level: float = None
    second_level: float = 0


@dataclass
class PlotData:
    field_vwsh: xr.DataArray
    first_level: Literal[1000, 3000, 6000]
    second_level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        first_level: float,
        second_level: float = 0,
) -> PlotData:
    plot_logger.debug(f"loading vwsh {first_level}-{second_level}m...")
    level_vwsh_info = deepcopy(vwsh_info)
    level_vwsh_info.level_type = "heightAboveGroundLayer"
    level_vwsh_info.level = {
        "first_level": first_level,
        "second_level": second_level,
    }
    vwsh_field = data_loader.load(
        field_info=level_vwsh_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    plot_logger.debug("calculating...")
    vwsh_field = apply_to_xarray_values(vwsh_field, lambda x: smth9(x, 0.5, -0.25, False))
    vwsh_field = apply_to_xarray_values(vwsh_field, lambda x: smth9(x, 0.5, -0.25, False))
    vwsh_field = apply_to_xarray_values(vwsh_field, lambda x: smth9(x, 0.5, -0.25, False))

    plot_logger.debug("loading done")

    return PlotData(
        field_vwsh=vwsh_field,
        first_level=first_level,
        second_level=second_level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    vwsh_field = plot_data.field_vwsh

    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range
    first_level = plot_metadata.first_level
    second_level = plot_metadata.second_level

    # style: levels 由数据范围按 NCL nice-values 算法运行时计算，色标取自样式库
    style_registry = get_default_registry()
    vwsh_style = style_registry.get_style("shr", "cn_fill")
    vwsh_line_style = style_registry.get_style("shr", "cn_line")

    min_value = vwsh_field.min().values
    max_value = vwsh_field.max().values
    level_setting = calculate_levels_automatic(
        min_value=min_value,
        max_value=max_value,
        max_count=len(vwsh_style.colors.colors),
        outside=False,
    )
    plot_logger.debug(f"value range: {min_value} {max_value}")
    plot_logger.debug(f"auto level: {level_setting}")
    vwsh_levels = np.arange(level_setting.min_value, level_setting.max_value + level_setting.step, level_setting.step)
    vwsh_color_map = mcolors.ListedColormap(vwsh_style.colors(np.arange(0, len(vwsh_levels) + 1)), "final_color_map")

    vwsh_style.levels = vwsh_levels
    vwsh_style.colors = vwsh_color_map
    vwsh_line_style.levels = vwsh_levels

    # create domain
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=area_range)
    graph_name = f"{area_name} {int(second_level/1000)}-{int(first_level/1000)}km shear (m/s)"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_vwsh = plot_data.field_vwsh

    # plot
    panel = Panel(domain=domain)
    panel.plot(plot_field_vwsh, style=vwsh_style)
    panel.plot(plot_field_vwsh, style=vwsh_line_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=vwsh_style)

    return panel
