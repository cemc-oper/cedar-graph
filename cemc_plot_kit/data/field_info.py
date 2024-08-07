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


# 2米温度
t_2m_info = FieldInfo(
    name="t2m",
    parameter=Parameter(
        eccodes_short_name="2t",
    ),
)


# 温度
t_info = FieldInfo(
    name="t",
    parameter=Parameter(
        eccodes_short_name="t",
    )
)


# 位势高度
hgt_info = FieldInfo(
    name="h",
    parameter=Parameter(
        eccodes_short_name="gh",
    )
)


# 海平面气压
mslp_info = FieldInfo(
    name="mslp",
    parameter=Parameter(
        eccodes_short_name="prmsl",
    )
)


# 东西风
u_info = FieldInfo(
    name="u",
    parameter=Parameter(
        eccodes_short_name="u",
    )
)


# 南北风
v_info = FieldInfo(
    name="v",
    parameter=Parameter(
        eccodes_short_name="v",
    )
)


# 雷达组合反射率
cr_info = FieldInfo(
    name="cr",
    parameter=Parameter(
        wgrib2_name="CR",
        # eccodes_keys=dict(
        #     disicpline=0,
        #     parameterCategory=16,
        #     parameterNumber=224,
        # )
    )
)


apcp_info = FieldInfo(
    name="apcp",
    parameter=Parameter(
        wgrib2_name="APCP",
    )
)


asnow_info = FieldInfo(
    name="asnow",
    parameter=Parameter(
        wgrib2_name="ASNOW",
    )
)


# 散度
div_info = FieldInfo(
    name="div",
    parameter=Parameter(
        wgrib2_name="RELD"
    )

)


# K指数
k_index_info = FieldInfo(
    name="k",
    parameter=Parameter(
        wgrib2_name="KX",
    )
)


# CIN
cin_info = FieldInfo(
    name="cape",
    parameter=Parameter(
        wgrib2_name="CIN"
    )
)


# 最优抬升指数
bpli_info = FieldInfo(
    name="bpli",
    parameter=Parameter(
        wgrib2_name="BLI"
    )
)

# CAPE
cape_info = FieldInfo(
    name="cape",
    parameter=Parameter(
        wgrib2_name="CAPE"
    )
)

# 水汽通量散度
qv_div_info = FieldInfo(
    name="qv_div",
    parameter=Parameter(
        wgrib2_name="FRZR",
    )
)

# 露点温度
dew_t_info = FieldInfo(
    name="dpt",
    parameter=Parameter(
        wgrib2_name="DPT",
    )
)

# 假相当位温
pte_info = FieldInfo(
    name="pte",
    parameter=Parameter(
        wgrib2_name="EPOT",
    )
)

# 垂直风切变
vwsh_info = FieldInfo(
    name="vwsh",
    parameter=Parameter(
        eccodes_short_name="vwsh"
    )
)
