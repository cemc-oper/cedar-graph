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

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import qv_div_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    system_name: str = None
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    area_name: Optional[str] = None
    area_range: Optional[AreaRange]  = None
    level: float = None


@dataclass
class PlotData:
    field_qv_div: xr.DataArray
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
    field_qv_div = data_loader.load(
        field_info=qv_div_level_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug("calculating...")
    field_qv_div = field_qv_div * 10000000.0
    field_qv_div = apply_to_xarray_values(field_qv_div, lambda x: smth9(x, 0.5, -0.25, False))
    field_qv_div = apply_to_xarray_values(field_qv_div, lambda x: smth9(x, 0.5, -0.25, False))

    plot_logger.debug("loading done")

    return PlotData(
        field_qv_div=field_qv_div,
        level=level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
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

    # create domain
    if area_range is None:
        domain = EastAsiaMapTemplate()
        graph_name = f"{level}hPa Moisture Divergence(10$^{{-7}}$g/hPa cm$^{{2}}s$,shadow)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} {level}hPa Moisture Divergence(10$^{{-7}}$g/hPa cm$^{{2}}s$,shadow)"

    # prepare data
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_qv_div = plot_data.field_qv_div

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_qv_div, style=qv_div_style)
    panel.plot(plot_field_qv_div, style=qv_div_line_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=qv_div_style)
    plot_logger.debug("plotting...done")

    return panel
