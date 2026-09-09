from dataclasses import dataclass


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
