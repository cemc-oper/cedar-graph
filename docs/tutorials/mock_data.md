---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# 使用 mock 数据

cedar-graph 的真实使用场景是从 CMA-HPC 上读取 GRIB2 文件，
但在测试、CI 和文档中我们希望任何环境都能画出图来。
{mod}`cedar_graph.testing` 子包提供了一个解析式的合成数据源
{class}`~cedar_graph.testing.MockDataSource`，可以无缝替换任何
绘图模块所需的真实数据源。

mock 测试套件 (`tests/mock/`) 与本文档样例都使用同一份 mock
数据，从而保证文档中看到的画图行为与 CI 验证的行为一致。

## 构造一个 mock 数据加载器

```{code-cell} python
import pandas as pd

from cedar_graph.testing import MockDataSource, build_mock_data_loader

# 直接构造一个 loader …
data_loader = build_mock_data_loader()

# … 或先创建数据源，便于复用或检查内容。
mock_source = MockDataSource(resolution=0.25)
```

`MockDataSource.retrieve` 根据 `field_info.name` 在覆盖东亚区域的
规则经纬度网格上生成一个 {class}`xarray.DataArray`：

```{code-cell} python
from cedar_graph.data.field_info import t_2m_info

start_time = pd.Timestamp("2024-07-01 00:00:00")
forecast_time = pd.Timedelta(hours=24)

field = mock_source.retrieve(
    field_info=t_2m_info,
    start_time=start_time,
    forecast_time=forecast_time,
)
field
```

## 驱动一个绘图模块

由于绘图模块只与 loader 交互，把 `MockDataSource` 换成
`LocalDataSource` 只需要改一行。下面这段代码与 `tests/mock/plots/cn/`
里的 pytest 用例几乎完全相同。

```{code-cell} python
from cedar_graph.plots.cn.t_2m.default import PlotMetadata, load_data, plot

plot_data = load_data(
    data_loader=data_loader,
    start_time=start_time,
    forecast_time=forecast_time,
)

metadata = PlotMetadata(
    start_time=start_time,
    forecast_time=forecast_time,
    system_name="CMA-GFS",
    sample_step=0.5,
)

panel = plot(plot_data=plot_data, plot_metadata=metadata)
panel.show()
```

## 字段名速查表

`MockDataSource` 主要按 {class}`~cedar_graph.data.FieldInfo` 中的
`name` 属性匹配解析公式；当 `name` 被多种物理量复用（CAPE 与 CIN
都使用 `cape`），还会回退到 `parameter.wgrib2_name` 区分。下表给出
mock 内置字段及其大致取值范围与物理特征。未列出的字段名会落到
通用的正弦余弦表达式上。

| 字段名 | 大致范围 | 物理特征 / 物理动机 | 涉及的绘图 |
|------|--------|--------------------|-----------|
| `t2m`  | 暖季 12–34 °C；冷季 −18..22 °C | 随 `start_time.month` 切换季节，叠加海陆对比 | `t_2m` |
| `t` (pl) | 850 hPa ≈ 270 K，500 hPa ≈ 240 K | 由表面温度 + 标准大气递减率（6.5 K/km）随气压层变化 | `t_dew_t`、各高度温度 |
| `rh2m` | 25–98 % | 东南偏湿、内陆偏干 | `rh_2m` |
| `h`    | 850 hPa ≈ 1500 gpm，500 hPa ≈ 5500 gpm | 由静力学厚度公式得到，叠加经向梯度 + 槽脊波列 | `height_500_*` |
| `mslp` | 默认夏季：陆地热低压 + 太平洋副高；冬季反之 | 随 `start_time.month` 切换 | `height_500_mslp` |
| `u`、`v` | 10 m: 0–12 m/s；高空: 0–30 m/s | 10 m 为季风南风；气压层为中纬度西风急流 + 低层 SW 急流舌 | 各类风场图 |
| `cr`   | 大部分 <10 dBZ；对流带 30–60 dBZ | 沿梅雨锋走向的窄带对流加两个嵌入强单体 | `radar_reflectivity` |
| `apcp` | 24h: 弱降水带 ~10–30 mm，强中心 >100 mm | 与雷达反射率同位相，依赖 `forecast_time` | `rain_24h`、`rain_wind_10m`、`prep_24h` |
| `asnow` | 0–~10 mm（24h），仅中高纬 | 高纬度冷区为主，南方为雨 | `prep_24h` |
| `div`  | −45e-5 .. +15e-5 s⁻¹ | 降水带为辐合，南侧为弱辐散 | `div_wind` |
| `k`    | 0–45 °C | 南方高、北方低 | `k_wind` |
| `cape` | 局地 0–2500 J/kg | 偏南海域热中心叠加小尺度背景 | `cape_wind` |
| CIN（同 `cape` 名）| 0–200 J/kg | 与 CAPE 互补：活跃区低、外围高 | `cin_wind` |
| `bli`  | −48..+5 K | 不稳定性向南增大 | `bli_wind` |
| `pte`  | 305–355 K | 随气压层变化，使 PTE(500)−PTE(850) 覆盖填色范围 | `pte_wind` |
| `vwsh` | 4–22 m/s | 中纬度急流区切变最大 | `shr` |
| `dpt`  | 由 `t_pressure` − 露点差得到，差值 0–30 K | 东南方向露点差最小（最饱和） | `t_dew_t` |
| `qv_div` | −45e-7 .. +8e-7 | 降水带为水汽辐合 | `qv_div` |
