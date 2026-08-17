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

# 配方编写指南

cedar-graph 的多数图形由 **YAML 配方**驱动：配方声明"加载哪些场、
做什么变换、按什么样式画哪些图层"，绘图流水线（domain 选择 →
数据预处理 → 逐层绘制 → 标题/色标）由 cedarkit-plots 的
{class}`~cedarkit.plots.engine.engine.PlotEngine` 统一执行。
新增一个图种通常只需要新增一个 `.yaml` 文件，不需要写 Python 代码。

本文先逐段介绍配方 schema，再给出**从 YAML 到出图的完整
walkthrough**（可直接执行复现）。

## 配方结构

以 `recipes/cn/h_500_psl.yaml`（500 hPa 高度场 + 海平面气压）为例：

```yaml
name: "500 hPa Height(10gpm), Sea Level Pressure(hPa,shadow)"
domain: { default: east_asia, area: cn_area }

data:
  h_500:
    field: h
    level: { first_level_type: 100, first_level: 500 }   # isobaricInhPa 500
    transforms:
      - { op: style_units }                              # dagpm：gpm -> 10gpm
      - { op: smth9, args: [0.5, 0.25, false], repeat: 4 }
  psl:
    field: mslp
    transforms:
      - { op: style_units }                              # hPa：Pa -> hPa
      - { op: smth9, args: [0.5, -0.25, false], repeat: 2 }

layers:
  - field: psl
    style: psl:cn
  - field: h_500
    style: h_500:cn_dagpm

title: { graph_name: "500 hPa Height(10gpm), Sea Level Pressure(hPa,shadow)" }
colorbar: { layer: 0 }
```

### domain

`default` / `area` 两个域模板名，按 `metadata.area_range` 是否为空选择。
内置模板：`east_asia`（东亚）、`cn_area`（自定义区域）。

### data

每个条目是一条"取数 + 加工"声明，`field` 与 `compute` 恰好二选一：

- `field` — 业务字段名，必须在引擎的字段注册表中
  （cedar-graph 的注册表是 {data}`~cedar_graph.recipes.engine.FIELD_INFOS`，
  键为 cemc 要素名：`t2m`、`h`、`mslp`、`u`、`v`、`apcp` …）；
- `level` — 层次选择，`first_level_type` 用 GRIB2 码表 4.5 数值码，
  `first_level` 可写 `"{param}"` 模板在运行时解析；
- `transforms` — 顺序执行的 transform op 链，每项
  `{ op, args, kwargs, repeat }`；
- `compute` — 从其它 data 条目派生新场的 compute op：
  `{ op, inputs, args, kwargs, outputs }`。`outputs` 支持多输出
  （如 `prep_classify` 把总降水拆成雨/雨夹雪/雪三场）。

### layers

绘制顺序即列表顺序。每层是 `field: <data 键>`（标量场）或
`vector: { u, v }`（风矢量对），加 `style`：

- `"id"` / `"id:variant"` — 直接引用样式库条目；
- `select` 规则 — 运行时按元数据选变体，`by` 是元数据上的点路径
  （`start_time.month`、`interval` 等；`Timedelta` 按整数小时比较），
  `cases` 键为逗号分隔的取值列表，**必须含 `else` 兜底**：

```yaml
layers:
  - field: t2m
    style:
      select:
        by: start_time.month
        cases:
          "5,6,7,8,9": t2m:cn_summer
          else: t2m:cn_winter
```

### params

配方参数，出现在生成的 `PlotMetadata` 与 `load_data` 签名上：

```yaml
params:
  wind_level: { type: float, required: true }     # 必需参数不可有默认值
  interval: { type: timedelta, default: 24h }     # 类型：float/int/str/timedelta
```

参数值经 `"{param}"` 模板注入 level、transform args 与标题。
整串模板保留原类型（`pd.Timedelta` 等），嵌入式模板按字符串格式化。

### title 与 colorbar

`title.graph_name` 支持元数据字段与三个内置变量：
`{forecast_hour}`（预报时效整数小时）、`{interval_hour}`、
`{previous_forecast_hour}`（= forecast − interval，降水时段标题用）。
`area_prefix: true` 时在自定义区域前拼 `"{area_name} "`。

`colorbar.layer` 指定为哪些图层的样式生成色标，单个索引或索引列表
（多图层色标，如 `prep_24h` 的 `{ layer: [0, 2, 1] }`）。

## op 词汇表

配方中不允许内嵌表达式（设计决策 D4，封闭词汇表），数据加工只能
通过已注册的 op。op 分两类，混用会在**加载期**报错：

| op | 类别 | 说明 |
|---|---|---|
| `style_units` | transform | 按该图层样式的 `units` 声明换算单位 |
| `unit_scale` / `unit_offset` | transform | 乘 scale / 加 offset |
| `smth9` | transform | NCL 九点平滑（cedarkit-comp），支持 `repeat` |
| `time_diff` | transform | 与 `forecast_time − interval` 的原始场求差（累计量转时段量） |
| `wind_speed` | compute | u/v 合成风速（cedar-graph 注册） |
| `prep_classify` | compute | 按雪雨比拆分雨/雨夹雪/雪（多输出，cedar-graph 注册） |

业务方可用
{meth}`~cedarkit.plots.engine.ops.OpRegistry.register`
在引擎上注册自己的诊断 op（参考
{func}`~cedar_graph.recipes.engine.create_op_registry`）。
每个 op 都会收到 {class}`~cedarkit.plots.engine.ops.OpContext`
（样式注册表、元数据、原始场重载器 `loader`）。

## 加载期校验

`PlotEngine.load_recipe` 在加载时做结构校验（schema，
{class}`~cedarkit.plots.engine.recipe.RecipeError` 报错含文件路径，
语法错误含行/列号）与交叉引用校验：未知 op / field / style id /
变体 / domain 都会在加载期失败，而不是等到画图时。

## Walkthrough：从 YAML 到出图

下面完整演示新增一个"850 hPa 温度"图形：写一个配方文件，用
cedar-graph 的配方引擎加载，再用 mock 数据渲染出图。

**第 1 步：写配方 YAML**

```{code-cell} python
from pathlib import Path
import tempfile

recipe_text = """\
name: "850 hPa Temperature (C)"
domain: { default: east_asia, area: cn_area }

data:
  t850:
    field: t                                        # 业务字段名（FIELD_INFOS 注册）
    level: { first_level_type: 100, first_level: 850 }  # isobaricInhPa 850
    transforms:
      - { op: unit_offset, args: [-273.15] }        # K -> °C

layers:
  - field: t850
    style: t          # cedarkit-plots 内置温度样式：levels 按数据范围生成

title: { graph_name: "850 hPa Temperature (C)" }
colorbar: { layer: 0 }
"""

work_dir = Path(tempfile.mkdtemp())
recipe_path = work_dir / "t850.yaml"
recipe_path.write_text(recipe_text, encoding="utf-8")
```

**第 2 步：引擎加载并适配为绘图模块接口**

```{code-cell} python
from cedar_graph.recipes.engine import get_recipe_engine

engine = get_recipe_engine()
recipe = engine.load_recipe(recipe_path)   # 加载期完成 schema + 交叉引用校验
plot_module = engine.build_module(recipe)  # -> PlotMetadata / load_data / plot
```

**第 3 步：加载数据并出图**

```{code-cell} python
import pandas as pd

from cedar_graph.testing import build_mock_data_loader

start_time = pd.Timestamp("2024-07-01 00:00:00")
forecast_time = pd.Timedelta(hours=24)

data_loader = build_mock_data_loader()
plot_data = plot_module.load_data(
    data_loader=data_loader,
    start_time=start_time,
    forecast_time=forecast_time,
)
metadata = plot_module.PlotMetadata(
    start_time=start_time,
    forecast_time=forecast_time,
    system_name="CMA-GFS",
    sample_step=0.5,
)
panel = plot_module.plot(plot_data=plot_data, plot_metadata=metadata)
panel.show()
```

在 CMA-HPC 上，同一份配方无需注册即可被
{func}`~cedar_graph.quickplot.quick_plot` 使用（把配方放到
`cedar_graph/recipes/cn/` 下，plot_type 即相对路径 `cn.t850`）；
cemc-plots-kit 的 task YAML 还可以直接引用**外部配方文件路径**，
不发版就能加图——详见 cemc-plots-kit 的 README 与 `examples/`。

## 何时仍需要 Python 模块

配方表达不下的诊断逻辑（多条
件分支、数据驱动的动态层次计算等）回退到 Python 绘图模块——
`cedar_graph.plots.cn` 下保留的 5 个逃生舱（`shr`、`qv_div`、
`div_wind`、`pte_wind`、`t_dew_t`）即属此类。纪律是"表达不下回退
Python，不扩 schema"（设计文档 §4.5）。
