from pathlib import Path
from typing import Union, Optional, Callable
from abc import ABC, abstractmethod

import xarray as xr
import pandas as pd

from reki.data_finder import find_local_file
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


data_mapper = {
    "CMA-MESO": "cma_meso_3km",
    "CMA-GFS": "cma_gfs_gmf",
    "CMA-TYM": "cma_tym",
    "CMA-GEPS": "cma_geps",
    "CMA-REPS": "cma_reps",
    "CMA-MESO-1KM": "cma_meso_1km",
}


def get_file_path(system_name, start_time, forecast_time, **kwargs) -> Union[str, Path]:
    """
    Get file path using embedded system config files for CEMC systems.

    Parameters
    ----------
    system_name
    start_time
    forecast_time
    kwargs

    Returns
    -------
    Path or None
        file path if found, None if not.
    """
    data_type_system_name = data_mapper[system_name]
    file_path = find_local_file(
        f"{data_type_system_name}/grib2/orig",
        start_time=start_time,
        forecast_time=forecast_time,
        **kwargs,
    )
    return file_path


class LocalDataSource(DataSource):
    """
    Data source for local files in CMA HPC system 1.

    Notes
    -----
    use embedded config files in reki by default.
    For other data source, please set ``file_path_func`` when object created.
    """
    def __init__(self, system_name: str, file_path_func: Optional[Callable] = None):
        super().__init__()
        self.system_name = system_name
        if file_path_func is None:
            self.find_path_func = get_file_path
        else:
            self.find_path_func = file_path_func

    def retrieve(
            self, field_info: FieldInfo,
            start_time: pd.Timestamp,
            forecast_time: pd.Timedelta,
            **kwargs,
    ) -> xr.DataArray or None:
        file_path = self.find_path_func(
            system_name=self.system_name,
            start_time=start_time,
            forecast_time=forecast_time,
            **kwargs,
        )
        field = get_field_from_file(field_info=field_info, file_path=file_path)
        return field
