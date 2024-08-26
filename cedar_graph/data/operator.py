from typing import Optional

import xarray as xr
import numpy as np

from cedarkit.maps.util import AreaRange


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
    extracted_array = field.sel(
        longitude=slice(area.start_longitude, area.end_longitude),
        latitude=slice(area.end_latitude, area.start_latitude),
    )
    return extracted_array


def sample_nearest(field: xr.DataArray, longitude_step: float, latitude_step: Optional[float]=None) -> xr.DataArray:
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
