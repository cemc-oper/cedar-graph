from dataclasses import dataclass


@dataclass
class BasePlotMetadata:
    auto_extract_area: bool = True
    auto_sample_nearest: bool = True
    sample_step: float = 0.09
