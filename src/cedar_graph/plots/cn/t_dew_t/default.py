from dataclasses import dataclass
from copy import deepcopy

import pandas as pd
import xarray as xr

from cedarkit.plots.style import get_default_registry
from cedarkit.plots.chart import Panel
from cedarkit.plots.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.plots.types import AreaRange

from cedarkit.comp.smooth import smth9
from cedarkit.comp.util import apply_to_xarray_values

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import t_info, dew_t_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    system_name: str = None
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    area_name: str = None
    area_range: AreaRange = None
    level: float = None


@dataclass
class PlotData:
    field_t: xr.DataArray
    field_t_dew_t_diff: xr.DataArray
    level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        level: float,
) -> PlotData:
    plot_logger.debug(f"loading t {level}hPa...")
    t_level_info = deepcopy(t_info)
    t_level_info.level_type = "pl"
    t_level_info.level = level
    field_t = data_loader.load(
        field_info=t_level_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    plot_logger.debug(f"loading dpt {level}hPa...")
    dew_t_level_info = deepcopy(dew_t_info)
    dew_t_level_info.level_type = "pl"
    dew_t_level_info.level = level
    field_dew_t = data_loader.load(
        field_info=dew_t_level_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    plot_logger.debug("calculating...")
    field_t_dew_t_diff = field_t - field_dew_t
    field_t_dew_t_diff = apply_to_xarray_values(field_t_dew_t_diff, lambda x: smth9(x, 0.5, 0.25, True))
    field_t_dew_t_diff = apply_to_xarray_values(field_t_dew_t_diff, lambda x: smth9(x, 0.5, 0.25, True))

    field_t = field_t - 273.15
    field_t = apply_to_xarray_values(field_t, lambda x: smth9(x, 0.5, 0.25, True))
    field_t = apply_to_xarray_values(field_t, lambda x: smth9(x, 0.5, 0.25, True))

    plot_logger.debug("loading done")

    return PlotData(
        field_t=field_t,
        field_t_dew_t_diff=field_t_dew_t_diff,
        level=level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata):
    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range
    level = plot_metadata.level

    # style
    style_registry = get_default_registry()
    t_dew_t_diff_style = style_registry.get_style("t_dew_t", "cn_fill")
    t_dew_t_diff_line_style = style_registry.get_style("t_dew_t", "cn_line")
    t_line_style = style_registry.get_style("t_dew_t", "cn_t")

    # create domain
    if area_range is None:
        domain = EastAsiaMapTemplate()
        graph_name = fr"{level}hPa Temperature($^\circ$C) and Dew Temperature Diff.($^\circ$C,shadow)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = fr"{area_name} {level}hPa Temperature($^\circ$C) and Dew Temperature Diff.($^\circ$C,shadow)"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_t_dew_t_diff = plot_data.field_t_dew_t_diff
    plot_field_t = plot_data.field_t

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_t_dew_t_diff, style=t_dew_t_diff_style)
    panel.plot(plot_field_t_dew_t_diff, style=t_dew_t_diff_line_style)
    panel.plot(plot_field_t, style=t_line_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=t_dew_t_diff_style)
    plot_logger.debug("plotting...done")

    return panel
