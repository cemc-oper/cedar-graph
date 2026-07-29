import importlib
import inspect
import types
from typing import Union, Callable, Any, Optional
from dataclasses import dataclass, fields

import pandas as pd

from cedar_graph.data import LocalDataSource, DataSource, DataLoader
from cedarkit.plots.types import AreaRange


# set_default_map_loader_package("cedarkit.plots.map.cemc")


@dataclass
class Metadata:
    ...


def quick_plot(
        plot_type: str,
        system_name: str,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        data_class: str = "od",
        storage_base: Optional[str] = None,
        data_source_kwargs: Optional[dict[str, Any]] = None,
        **plot_kwargs,
):
    """
    draw the plot and display it

    Parameters
    ----------
    plot_type
        Plot type. Use plots in cedar-graph package, plot_type is a module named "cedar_graph.plots.{plot_type}".
    system_name
        system name. default supported systems:

        * CMA-GFS：global forecast system
        * CMA-MESO：regional system (3km)
        * CMA-TYM：regional typhoon forecast system
        * CMA-MESO-1KM：regional forecast system (1km)
    start_time
        start time, such as YYYY-MM-DD HH:00:00
    forecast_time
        forecast time, such as 24h
    data_class
        data class passed to reki data finder, default is "od".
    storage_base
        storage base path passed to reki data finder.
    data_source_kwargs
        other keyword arguments passed to reki data finder.
    plot_kwargs
        other plot-specific parameters, such as ``area_range``, ``interval``.
    """
    plot_settings = dict(
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
        **plot_kwargs,
    )
    data_source_config = dict(
        data_class=data_class,
        storage_base=storage_base,
        **(data_source_kwargs or {}),
    )
    show_plot(
        plot_type=plot_type,
        plot_settings=plot_settings,
        data_source_config=data_source_config,
    )


def show_plot(plot_type: str, plot_settings: dict, data_source_config: dict):
    plot_module = get_plot_module(plot_type=plot_type)
    metadata_class = Metadata
    metadata = create_metadata(
        metadata_class=metadata_class,
        plot_settings=plot_settings,
        processor_map=item_processor_map
    )

    data_source = create_data_source(
        system_name=metadata.system_name,
        data_source_config=data_source_config,
    )

    # data source -> data field
    plot_data = load(
        metadata=metadata,
        load_data_func=plot_module.load_data,
        data_source=data_source,
    )

    # field -> plot
    plot_func = plot_module.plot
    plot_metadata = plot_module.PlotMetadata
    convert_metadata(from_metadata=metadata, to_metadata=plot_metadata)
    panel = plot_func(
        plot_data=plot_data,
        plot_metadata=plot_metadata,
    )

    # plot -> output
    panel.show()


def load(metadata, load_data_func: Callable, data_source: DataSource):
    data_loader = DataLoader(data_source=data_source)

    load_data_params = inspect.signature(load_data_func).parameters
    load_data_kwargs = {
        k: v for k, v in metadata.__dict__.items()
        if k in load_data_params
    }
    plot_data = load_data_func(
        data_loader=data_loader,
        **load_data_kwargs,
    )
    return plot_data


def create_data_source(system_name: str, data_source_config: dict) -> DataSource:
    data_source = LocalDataSource(system_name=system_name, **data_source_config)
    return data_source


def get_plot_module(plot_type: str, base_module_name: str = "cedar_graph.plots") -> types.ModuleType:
    """
    Return plot module basd on plot type.

    Parameters
    ----------
    plot_type
        plot type
    base_module_name
        base module name
    Returns
    -------
    types.ModuleType
        plot module
    """
    plot_module = importlib.import_module(f"{base_module_name}.{plot_type}")
    return plot_module


def get_metadata_class(plot_module: types.ModuleType):
    """
    get ``PlotMetadata`` class from plot module.

    Parameters
    ----------
    plot_module


    Returns
    -------
    PlotMetadata
        A ``PlotMetadata`` class from ``plot_module``.
    """
    metadata_class = plot_module.PlotMetadata
    return metadata_class


def convert_metadata(from_metadata, to_metadata):
    """
    Fill one metadata object (``to_metadata``) properties with
    corresponding properties in another metadata (``from_metadata``).

    Parameters
    ----------
    from_metadata
    to_metadata

    """
    names = set([f.name for f in fields(to_metadata)])
    for k, v in from_metadata.__dict__.items():
        if k in names:
            setattr(to_metadata, k, v)


def create_metadata(metadata_class, plot_settings: dict[str, Any], processor_map: dict[str, Callable]):
    """
    Create a Metadata object, fill properties with all keys in dict.

    Parameters
    ----------
    metadata_class
        metadata class reference.
    plot_settings
        Properties to be filled in Metadata object. No nested dict.
    processor_map
        A function mapper to process item in dict.

    Returns
    -------
    Metadata
        A Metadata object with properties from dict.
    """
    metadata = metadata_class()

    for key in plot_settings.keys():
        value = plot_settings[key]
        if key in processor_map:
            parsed_value = processor_map[key](value)
        else:
            parsed_value = value
        setattr(metadata, key, parsed_value)

    return metadata


def process_start_time(item: Union[str, pd.Timestamp]) -> pd.Timestamp:
    """
    convert item to timestamp object.

    Parameters
    ----------
    item

    Returns
    -------
    pd.Timestamp
    """
    parsed_item = None
    if isinstance(item, str):
        if len(item) == 10:
            parsed_item = pd.to_datetime(item, format="%Y%m%d%H")
        elif len(item) == 12:
            parsed_item = pd.to_datetime(item, format="%Y%m%d%H%M")
        else:
            parsed_item = pd.to_datetime(item)
    elif isinstance(item, pd.Timestamp):
        parsed_item = item
    else:
        raise ValueError("type is not supported")

    return parsed_item


def process_forecast_time(item: Union[str, pd.Timedelta]) -> pd.Timedelta:
    """
    convert itme to timedelta object.

    Parameters
    ----------
    item

    Returns
    -------
    pd.Timedelta
    """
    parsed_item = None
    if isinstance(item, str):
        parsed_item = pd.to_timedelta(item)
    elif isinstance(item, pd.Timestamp):
        parsed_item = item
    else:
        raise ValueError("type is not supported")

    return parsed_item


def process_area_range(item: Union[dict, AreaRange]) -> AreaRange:
    """
    convert item to ``AreaRange`` object.

    Parameters
    ----------
    item

    Returns
    -------
    AreaRange
    """
    parsed_item = None
    if isinstance(item, dict):
        parsed_item = AreaRange(**item)
    elif isinstance(item, AreaRange):
        parsed_item = item
    else:
        raise ValueError("type is not supported")

    return parsed_item


item_processor_map = dict(
    start_time=process_start_time,
    forecast_time=process_forecast_time,
    area_range=process_area_range,
    interval=process_forecast_time,
)
