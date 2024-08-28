from dataclasses import fields

from typing import Optional

import xarray as xr
import numpy as np

from cedarkit.maps.util import AreaRange

from cedar_graph.metadata import BasePlotMetadata


def prepare_data(plot_data, plot_metadata: BasePlotMetadata, total_area: AreaRange):
    """
    Process all fields in plot_data according setting in plot_metadata.
    Use generated fields replace those in plot_data.

    Supported operators:

    * extract_area: use ``total_area``
    * sample_nearest: use ``plot_metadata.sample_step``

    Parameters
    ----------
    plot_data
        some PlotData object for each plot.
    plot_metadata
        some PlotMetadata object for each plot.
    total_area
        used when auto_extract_area is set.

    Returns
    -------
    PlotData
    """
    auto_extract_area = plot_metadata.auto_extract_area
    auto_sample_nearest = plot_metadata.auto_sample_nearest

    field_names = set([
        f.name for f in fields(plot_data)
        if f.type == xr.DataArray and f.name.index("field_") != -1
    ])

    if auto_extract_area:
        for field_name in field_names:
            field = getattr(plot_data, field_name)
            plot_field = extract_area(field, area=total_area)
            setattr(plot_data, field_name, plot_field)

    if auto_sample_nearest:
        sample_step = plot_metadata.sample_step
        for field_name in field_names:
            field = getattr(plot_data, field_name)
            plot_field = sample_nearest(field, longitude_step=sample_step, latitude_step=sample_step)
            setattr(plot_data, field_name, plot_field)

    return plot_data


def extract_area(field: xr.DataArray, area: AreaRange) -> xr.DataArray:
    """
    extract field with area range.

    Parameters
    ----------
    field
    area

    Returns
    -------
    xr.DataArray
    """
    longitude_range = slice(area.start_longitude, area.end_longitude)
    latitude_range = slice(area.end_latitude, area.start_latitude)
    extracted_array = field.sel(
        longitude=longitude_range,
        latitude=latitude_range,
    )
    return extracted_array


def sample_nearest(field: xr.DataArray, longitude_step: float, latitude_step: Optional[float]=None) -> xr.DataArray:
    """
    Sample field nearest to longitude and latitude step.
    If field step is larger, return the original field without any change.

    Parameters
    ----------
    field
    longitude_step
        target longitude step, unit degree
    latitude_step
        target latitude step, unit degree

    Returns
    -------
    xr.DataArray

    """
    if latitude_step is None:
        latitude_step = longitude_step

    lat = field[field.dims[0]]
    data_lat_step = abs(lat[0] - lat[1]).values
    lon = field[field.dims[1]]
    data_lon_step = abs(lon[0] - lon[1]).values

    lat_ratio = int(np.round(latitude_step / data_lat_step))
    lat_ratio = 1 if lat_ratio < 1 else lat_ratio
    lon_ratio = int(np.round(longitude_step / data_lon_step))
    lon_ratio = 1 if lon_ratio < 1 else lon_ratio

    if lat_ratio == 1 and lon_ratio == 1:
        return field
    else:
        sampled_field = field[::lat_ratio, ::lon_ratio]
        return sampled_field
