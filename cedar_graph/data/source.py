from pathlib import Path
from typing import Union, Optional, Callable
from abc import ABC, abstractmethod

import xarray as xr
import pandas as pd

import reki
from reki.sources.local import LocalSource

from .field_info import FieldInfo


class DataSource(ABC):
    """
    An abstract base class for data source.
    """
    def __init__(self):
        ...

    @abstractmethod
    def retrieve(
            self,
            field_info: FieldInfo,
            start_time: pd.Timestamp,
            forecast_time: pd.Timedelta,
    ) -> Optional[xr.DataArray]:
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
    grib_field = reki.from_source("file", file_path).sel(
        parameter=field_info.parameter.get_parameter(),
        level_type=field_info.level_type,
        level=field_info.level,
        **additional_keys,
    ).first()
    if grib_field is None:
        return None
    return grib_field.to_xarray()


data_mapper = {
    "CMA-GFS": "cma_gfs_gmf",
    "CMA-GEPS": "cma_geps",
    "CMA-MESO": "cma_meso_1km",
    "CMA-MESO-1KM": "cma_meso_1km",
    "CMA-MESO-3KM": "cma_meso_3km",
    "CMA-REPS": "cma_reps",
    "CMA-TYM": "cma_tym",
}


def get_file_path(system_name: str, start_time, forecast_time, **kwargs) -> Union[str, Path]:
    """
    Get file path using embedded system config files for CEMC systems.

    Parameters
    ----------
    system_name
    start_time
    forecast_time
    kwargs
        other keyword arguments passed to ``LocalSource``
        (``data_class`` / ``storage_base`` / ...)

    Returns
    -------
    Path or None
        file path if found, None if not.
    """
    data_type_system_name = data_mapper[system_name]
    source = LocalSource(
        f"{data_type_system_name}/grib2/orig",
        start_time=start_time,
        forecast_time=forecast_time,
        **kwargs,
    )
    return source.resolve_path()


class LocalDataSource(DataSource):
    """
    Data source for local files in CMA HPC system 1.

    Notes
    -----
    use embedded config files in reki by default.
    For other data source, please set ``file_path_func`` when object created.
    """
    def __init__(
            self,
            system_name: str,
            data_class: str = "od",
            storage_base: Optional[str] = None,
            file_path_func: Optional[Callable] = None,
            data_source_kwargs: Optional[dict] = None,
    ):
        super().__init__()
        self.system_name = system_name
        self.data_class = data_class
        self.storage_base = storage_base
        self.data_source_kwargs = data_source_kwargs or {}
        if file_path_func is None:
            self.find_path_func = get_file_path
        else:
            self.find_path_func = file_path_func

    def retrieve(
            self,
            field_info: FieldInfo,
            start_time: pd.Timestamp,
            forecast_time: pd.Timedelta,
    ) -> Optional[xr.DataArray]:
        """
        Find the local file path using ``find_path_func()``,
        and load the field using  ``get_field_from_file()``

        Parameters
        ----------
        field_info
        start_time
        forecast_time

        Returns
        -------
        xr.DataArray or None
            field if found, None if not.
        """
        file_path = self.find_path_func(
            system_name=self.system_name,
            start_time=start_time,
            forecast_time=forecast_time,
            data_class=self.data_class,
            storage_base=self.storage_base,
            **self.data_source_kwargs,
        )
        field = get_field_from_file(field_info=field_info, file_path=file_path)
        return field
