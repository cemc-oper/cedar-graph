from dataclasses import dataclass
from typing import Union, Optional, Dict


@dataclass
class Parameter:
    eccodes_short_name: Optional[str] = None
    eccodes_keys: Optional[Dict[str, int]] = None
    wgrib2_name: Optional[str] = None
    cemc_name: Optional[str] = None

    def get_parameter(self) -> Optional[Union[str, Dict[str, int]]]:
        """
        Return proper item for ``parameter`` param in reki's load_* functions.

        Returns
        -------
        Optional[Union[str, Dict[str, int]]]
        """
        if self.eccodes_short_name is not None:
            return self.eccodes_short_name
        if self.eccodes_keys is not None:
            return self.eccodes_keys
        if self.wgrib2_name is not None:
            return self.wgrib2_name
        if self.cemc_name is not None:
            return self.cemc_name
        return None

@dataclass
class FieldInfo:
    name: str
    parameter: Parameter
    level_type: Optional[Union[str, Dict[str, int]]] = None
    level: Optional[Union[int, float, Dict[str, int]]] = None
    additional_keys: Optional[Dict[str, Union[str, int, float]]] = None


t_2m_info = FieldInfo(
    name="t2m",
    parameter=Parameter(
        eccodes_short_name="2t",
    ),
)
