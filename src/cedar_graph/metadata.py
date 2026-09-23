from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

from cedarkit.plots.workflow.plan import CompileContext


@dataclass(frozen=True)
class ProductMetadata:
    """Normalized input metadata shared by quick plots and product plans."""

    system_name: str
    start_time: pd.Timestamp
    forecast_time: pd.Timedelta
    params: Mapping[str, Any]

    @classmethod
    def from_settings(cls, settings: Mapping[str, Any]) -> "ProductMetadata":
        values = dict(settings)
        return cls(str(values.pop("system_name")), pd.Timestamp(values.pop("start_time")),
                   pd.Timedelta(values.pop("forecast_time")), values)

    def compile_context(self) -> CompileContext:
        return CompileContext(start_time=self.start_time, forecast_time=self.forecast_time,
                              params=dict(self.params))


@dataclass
class BasePlotMetadata:
    """
    Attributes
    ----------
    auto_extract_area : bool
        Flag for auto extract area. If True, data will be extract according to map range before drawing.
    auto_sample_nearest : bool
        Flag for auto sample data. If True, data will be regrid to a smaller grid nearest to ``sample_step``.
    sample_step : float
        A target grid resolution to use when ``auto_sample_nearest`` is set.
    """
    auto_extract_area: bool = True
    auto_sample_nearest: bool = True
    sample_step: float = 0.09
