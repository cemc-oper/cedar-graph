from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.maps.style import ContourStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cedarkit.comp.smooth import smth9
from cedarkit.comp.util import apply_to_xarray_values

from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import qv_div_info
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata:
    system_name: str = None
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    area_name: Optional[str] = None
    area_range: Optional[AreaRange]  = None
    level: float = None


@dataclass
class PlotData:
    qv_div_field: xr.DataArray
    level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        level: float,
        **kwargs,
) -> PlotData:
    plot_logger.debug(f"loading qv_div {level}hPa...")
    qv_div_level_info = deepcopy(qv_div_info)
    qv_div_level_info.level_type = "pl"
    qv_div_level_info.level = level
    qv_div_field = data_loader.load(
        field_info=qv_div_level_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug("calculating...")
    qv_div_field = qv_div_field * 10000000.0
    qv_div_field = apply_to_xarray_values(qv_div_field, lambda x: smth9(x, 0.5, -0.25, False))
    qv_div_field = apply_to_xarray_values(qv_div_field, lambda x: smth9(x, 0.5, -0.25, False))

    return PlotData(
        qv_div_field=qv_div_field,
        level=level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    qv_div_field = plot_data.qv_div_field

    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
    if area_name is None:
        area_name = ""
    area_range = plot_metadata.area_range
    level = plot_metadata.level

    qv_div_levels = np.arange(-50, -5 + 5, step=5)
    qv_div_colormap = get_ncl_colormap("WhBlGrYeRe", count=len(qv_div_levels) + 1, spread_start=100 - 2, spread_end=2 - 2)

    qv_div_style = ContourStyle(
        colors=qv_div_colormap,
        levels=qv_div_levels,
        fill=True,
    )
    qv_div_line_style = ContourStyle(
        colors="black",
        levels=qv_div_levels,
        linewidths=0.2,
        linestyles="-",
        fill=False,
    )

    # plot
    if area_range is None:
        domain = EastAsiaMapTemplate()
        graph_name = f"{level}hPa Moisture Divergence(10$^{{-7}}$g/hPa cm$^{{2}}s$,shadow)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} {level}hPa Moisture Divergence(10$^{{-7}}$g/hPa cm$^{{2}}s$,shadow)"

    panel = Panel(domain=domain)
    panel.plot(qv_div_field[::10, ::10], style=qv_div_style)
    panel.plot(qv_div_field[::10, ::10], style=qv_div_line_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=qv_div_style)

    return panel
