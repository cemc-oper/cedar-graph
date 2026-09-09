from dataclasses import fields

import xarray as xr

from cedarkit.plots.types import AreaRange
from reki.operator import extract_region, sample_nearest

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

    if auto_sample_nearest:
        sample_step = plot_metadata.sample_step
        for field_name in field_names:
            field = getattr(plot_data, field_name)
            plot_field = sample_nearest(field, longitude_step=sample_step, latitude_step=sample_step)
            setattr(plot_data, field_name, plot_field)

    if auto_extract_area:
        for field_name in field_names:
            field = getattr(plot_data, field_name)
            plot_field = extract_area(field, area=total_area)
            setattr(plot_data, field_name, plot_field)

    return plot_data


def extract_area(field: xr.DataArray, area: AreaRange) -> xr.DataArray:
    """
    extract field with area range, padded by one grid step on each side.

    The padding keeps contour lines complete at the area boundary.
    Region extraction itself is delegated to
    ``reki.operator.extract_region``.

    Parameters
    ----------
    field
    area

    Returns
    -------
    xr.DataArray
    """
    lat_step = abs(field.latitude.values[1] - field.latitude.values[0])
    lon_step = abs(field.longitude.values[1] - field.longitude.values[0])
    return extract_region(
        field,
        start_longitude=area.start_longitude - lon_step,
        end_longitude=area.end_longitude + lon_step,
        start_latitude=area.start_latitude - lat_step,
        end_latitude=area.end_latitude + lat_step,
    )
