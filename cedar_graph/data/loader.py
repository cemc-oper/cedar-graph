import pandas as pd
import xarray as xr

from .field_info import FieldInfo
from .source import DataSource


class DataLoader:
    def __init__(self, data_source: DataSource):
        self.data_source = data_source

    def load(
            self,
            field_info: FieldInfo,
            start_time: pd.Timestamp,
            forecast_time: pd.Timedelta,
    ) -> xr.DataArray or None:
        """
        Load field from data loader.

        Parameters
        ----------
        field_info
        start_time
        forecast_time

        Returns
        -------
        xr.DataArray or None
        """
        field = self.data_source.retrieve(
            field_info=field_info,
            start_time=start_time,
            forecast_time=forecast_time,
        )
        return field
