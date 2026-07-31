from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

import xarray as xr
import pandas as pd
import numpy as np

from cedarkit.comp.smooth import smth9
from cedarkit.comp.util import apply_to_xarray_values

from cedarkit.plots.style import get_default_registry
from cedarkit.plots.chart import Panel
from cedarkit.plots.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.plots.types import AreaRange

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import hgt_info, u_info, v_info
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
    field_hgt_500: xr.DataArray
    field_u_850: xr.DataArray
    field_v_850: xr.DataArray
    field_wind_speed_850: xr.DataArray


def load_data(data_loader: DataLoader, start_time: pd.Timestamp, forecast_time: pd.Timedelta,
) -> PlotData:
    # data file -> data field
    plot_logger.debug("loading height 500hPa...")
    hgt_500_info = deepcopy(hgt_info)
    hgt_500_info.level_type = "pl"
    hgt_500_info.level = 500
    field_h_500 = data_loader.load(
        field_info=hgt_500_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    plot_logger.debug("loading u 850hPa...")
    u_850_info = deepcopy(u_info)
    u_850_info.level_type = "pl"
    u_850_info.level = 850
    field_u_850 = data_loader.load(
        field_info=u_850_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    plot_logger.debug("loading v 850hPa...")
    v_850_info = deepcopy(v_info)
    v_850_info.level_type = "pl"
    v_850_info.level = 850
    field_v_850 = data_loader.load(
        field_info=v_850_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    # data field -> plot data
    plot_logger.debug("calculating...")
    # 单位转换
    field_h_500 = field_h_500 / 10.
    # 平滑
    field_h_500 = apply_to_xarray_values(field_h_500, lambda x: smth9(x, 0.5, 0.25, False))
    field_h_500 = apply_to_xarray_values(field_h_500, lambda x: smth9(x, 0.5, 0.25, False))

    wind_speed_850_field = (np.sqrt(field_u_850 * field_u_850 + field_v_850 * field_v_850))

    plot_logger.debug("loading done")

    return PlotData(
        field_hgt_500=field_h_500,
        field_u_850=field_u_850,
        field_v_850=field_v_850,
        field_wind_speed_850=wind_speed_850_field,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name
    area_range = plot_metadata.area_range
    area_name = plot_metadata.area_name

    # style
    style_registry = get_default_registry()
    wind_speed_style = style_registry.get_style("ws_850")
    hgt_style = style_registry.get_style("h_500", "cn_ws")
    barb_style = style_registry.get_style("wind")

    # create domain
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=area_range)
    graph_name = "500 hPa HGT (10gpm), 850 hPa Wind and Wind Speed(m/s, shadow)"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_wind_speed_850 = plot_data.field_wind_speed_850
    plot_field_h_500 = plot_data.field_hgt_500
    plot_field_u_850 = plot_data.field_u_850
    plot_field_v_850 = plot_data.field_v_850

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_wind_speed_850, style=wind_speed_style)
    panel.plot(plot_field_h_500, style=hgt_style)
    panel.plot([[plot_field_u_850, plot_field_v_850]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=wind_speed_style)

    plot_logger.debug("plotting...done")

    return panel
