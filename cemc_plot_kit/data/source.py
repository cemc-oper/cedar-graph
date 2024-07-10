from pathlib import Path
from typing import Union, Optional
from abc import ABC, abstractmethod

import xarray as xr
import pandas as pd

from reki.format.grib.eccodes import load_field_from_file

from .field_info import FieldInfo


class DataSource(ABC):
    def __init__(self):
        ...

    @abstractmethod
    def retrieve(
            self, field_info: FieldInfo, start_time: pd.Timestamp, forecast_time: pd.Timedelta
    ) -> xr.DataArray or None:
        """
        Retrieve field from data source.

        Parameters
        ----------
        field_info
        start_time
        forecast_time

        Returns
        -------
        Optional[xr.DataArray]
        """
        ...


def get_field_from_file(field_info: FieldInfo, file_path: Union[str, Path]) -> Optional[xr.DataArray]:
    """
    Load field from local file according to field info.

    Parameters
    ----------
    field_info
        Field info.
    file_path
        local file path.

    Returns
    -------
    xr.DataArray
    """
    additional_keys = field_info.additional_keys
    if additional_keys is None:
        additional_keys = dict()
    field = load_field_from_file(
        file_path,
        parameter=field_info.parameter.get_parameter(),
        level_type=field_info.level_type,
        level=field_info.level,
        **additional_keys,
    )
    return field
