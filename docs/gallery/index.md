---
mystnb:
  execution_mode: 'off'
---

# 绘图样例

本节中的每一页都使用 {class}`cedar_graph.testing.MockDataSource`
（即 mock 测试套件所使用的同一份合成数据源）渲染出一张图。
图中的具体数值并不具备真实气象意义，而是用于完整跑通对应的
图种定义（YAML 配方或 Python 绘图模块：数据获取、预处理、样式、
面板组装、色标）所需的解析式合成场。

```{toctree}
:maxdepth: 1

t_2m
rh_2m
height_500_mslp
height_500_wind_850
wind_10m
radar_reflectivity
div_wind
k_wind
cape_wind
cin_wind
bli_wind
pte_wind
qv_div
shr
t_dew_t
rain_24h
rain_wind_10m
prep_24h
```
