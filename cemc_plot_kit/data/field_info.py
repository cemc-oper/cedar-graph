from dataclasses import dataclass
from typing import Union, Optional, Dict


@dataclass
class Parameter:
    eccodes_short_name: Optional[str] = None
    eccodes_keys: Optional[Dict[str, int]] = None
    wgrib2_name: Optional[str] = None
    cemc_name: Optional[str] = None


@dataclass
class FieldInfo:
    name: str
    parameter: Parameter
    level_type: Optional[Union[str, Dict[str, int]]] = None
    level: Optional[Union[int, float, Dict[str, int]]] = None


t_2m_info = FieldInfo(
    name="t2m",
    parameter=Parameter(
        eccodes_short_name="2t",
    ),
)
