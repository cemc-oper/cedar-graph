from dataclasses import dataclass
from copy import deepcopy

import pandas as pd
import xarray as xr

from cedar_graph.data.operator import prepare_data
from cedarkit.plots.style import get_default_registry
from cedarkit.plots.chart import Panel
from cedarkit.plots.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.plots.types import AreaRange

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import u_info, v_info, pte_info
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    system_name: str = None
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    area_name: str = None
    area_range: AreaRange = None
    wind_level: float = None
    pte_levels: tuple[float, float] = (500, 850)


@dataclass
class PlotData:
    field_pte: xr.DataArray
    field_u: xr.DataArray
    field_v: xr.DataArray
    wind_level: float
    pte_levels: tuple[float, float] = (500, 850)


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        wind_level: float,
        pte_levels: tuple[float, float],
) -> PlotData:
    first_pte_level = pte_levels[0]
    second_pte_level = pte_levels[1]

    plot_logger.debug(f"loading pte {first_pte_level}hPa...")
    first_pte_info = deepcopy(pte_info)
    first_pte_info.level_type = "pl"
    first_pte_info.level = first_pte_level
    field_first_pte = data_loader.load(
        field_info=first_pte_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    plot_logger.debug(f"loading pte {second_pte_level}hPa...")
    second_pte_info = deepcopy(pte_info)
    second_pte_info.level_type = "pl"
    second_pte_info.level = second_pte_level
    field_second_pte = data_loader.load(
        field_info=second_pte_info,
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
        forecast_time=forecast_time,
    )
    plot_logger.debug(f"loading u {wind_level}hPa...")
    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    field_v = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    plot_logger.debug("calculating...")
    field_pte = field_first_pte - field_second_pte

    return PlotData(
        field_pte=field_pte,
        field_u=field_u,
        field_v=field_v,
        wind_level=wind_level,
        pte_levels=pte_levels,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range
    wind_level = plot_metadata.wind_level
    pte_levels = plot_data.pte_levels

    # style
    style_registry = get_default_registry()
    pte_diff_style = style_registry.get_style("pte_diff", "cn_fill")
    pte_diff_line_style = style_registry.get_style("pte_diff", "cn_line")
    barb_style = style_registry.get_style("wind")

    # create domain
    if area_range is None:
        domain = EastAsiaMapTemplate()
        graph_name = f"PTE {pte_levels[0]}hPa-{pte_levels[1]}hPa(K,shadow) and {wind_level}hPa Wind(m/s)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} PTE {pte_levels[0]}hPa-{pte_levels[1]}hPa(K,shadow) and {wind_level}hPa Wind(m/s)"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_pte = plot_data.field_pte
    plot_field_u = plot_data.field_u
    plot_field_v = plot_data.field_v

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_pte, style=pte_diff_style)
    panel.plot(plot_field_pte, style=pte_diff_line_style)
    panel.plot([[plot_field_u, plot_field_v]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=pte_diff_style)
    plot_logger.debug("plotting...done")

    return panel
