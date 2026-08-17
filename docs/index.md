---
mystnb:
  execution_mode: 'off'
---

# cedar-graph

`cedar-graph` 是面向 CEMC 业务数值预报系统（CMA-GFS、CMA-MESO、CMA-TYM、
CMA-GEPS 等）输出的高级绘图库，构建在 `reki`、`cedarkit-comp`、
`cedarkit-plots` 之上，把"找数据 → 读数据 → 画图"封装成可直接复用的绘图模块。

## 主要特性

- **配方驱动的图形定义**：大多数图种由 `cedar_graph/recipes/cn/`
  下的 YAML 配方声明（数据、变换、图层、样式、标题），绘图流水线由
  cedarkit-plots 的绘图引擎统一执行；诊断复杂的图种保留 Python
  逃生舱模块。配方与模块对外暴露相同的
  `PlotMetadata` / `load_data` / `plot` 三件套接口，既可被
  `quick_plot` 调度，也可在脚本中直接驱动。
- **业务样式库**：CEMC 业务色标集中在 `cedar_graph/styles/cn/`
  的 YAML 样式文件中，经 entry point 注入 cedarkit-plots 的
  样式注册表。
- **数据源可替换**：图种定义只与 {class}`~cedar_graph.data.DataLoader`
  交互。CMA-HPC 上使用 {class}`~cedar_graph.data.LocalDataSource`
  读取真实 GRIB2 数据；测试与文档使用
  {class}`~cedar_graph.testing.MockDataSource` 生成合成场。
- **覆盖常见预报量**：地面要素、高空形势场、降水、对流参数、
  风切变等多种典型预报图。

## 快速上手

```python
from cedar_graph.quickplot import quick_plot

quick_plot(
    plot_type="cn.t2m",
    system_name="CMA-GFS",
    start_time="2024073000",
    forecast_time="48h",
)
```

更多用法见 {doc}`tutorials/quick_plot` 与 {doc}`tutorials/manual_plot`。

## 内容导览

- {doc}`getting_started/install` 与 {doc}`tutorials/quick_plot`：完成安装并跑通第一张图。
- {doc}`getting_started/concepts`、{doc}`tutorials/manual_plot`、{doc}`tutorials/mock_data`：
  深入讲解核心概念和不同的使用方式。
- {doc}`tutorials/recipe`、{doc}`tutorials/style_library`：编写自己的
  YAML 配方与业务样式。
- {doc}`gallery/index`：逐个展示全部支持的画图类型。
- {doc}`api/index`：`cedar_graph.data`、`cedar_graph.plots`、`cedar_graph.recipes`、
  `cedar_graph.quickplot` 以及测试工具的自动生成参考。

```{admonition} 文档约定
:class: tip

本文档中的所有示例图都在构建时由 {class}`cedar_graph.testing.MockDataSource`
动态生成的合成数据绘制，不依赖 CMA-HPC 上的真实业务数据，便于在任意环境
下重建本站。同一份模拟数据源也被 mock 测试套件复用，详见
{doc}`tutorials/mock_data`。
```

```{toctree}
:hidden:
:caption: 快速开始

getting_started/install
tutorials/quick_plot
```

```{toctree}
:hidden:
:caption: 用法

getting_started/concepts
tutorials/manual_plot
tutorials/mock_data
tutorials/recipe
tutorials/style_library
```

```{toctree}
:hidden:
:caption: 绘图样例

gallery/index
```

```{toctree}
:hidden:
:caption: 参考

api/index
changelog
```
