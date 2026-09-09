from typing import Optional

import pandas as pd
import xarray as xr

from .field_info import FieldInfo
from .source import DataSource
from .provider import RekiProvider


class DataLoader:
    """
    Load data from any data source.

    Attributes
    ----------
    data_source : DataSource
        some data source which is used to load the field.
    """
    def __init__(self, data_source: Optional[DataSource] = None,
                 provider: Optional[RekiProvider] = None):
        if (data_source is None) == (provider is None):
            raise TypeError("provide exactly one of data_source or provider")
        self.data_source = data_source
        self.provider = provider

    def load(
            self,
            field_info: FieldInfo,
            start_time: pd.Timestamp,
            forecast_time: pd.Timedelta,
            required: bool = True,
    ) -> Optional[xr.DataArray]:
        """
        Load field from some ``DataSource``.

        Parameters
        ----------
        field_info
            field info, including parameter, level type and level value.
        start_time
        forecast_time

        Returns
        -------
        xr.DataArray or None
        """
        if self.provider is not None:
            return self.provider.load(
                field_info.to_field_query(), start_time=start_time,
                forecast_time=forecast_time, required=required,
                parameter_id=field_info.parameter_id,
            )
        return self.data_source.retrieve(
            field_info=field_info, start_time=start_time,
            forecast_time=forecast_time,
        )
