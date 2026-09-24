# cedar-graph

![Maturity-Sandbox](https://img.shields.io/badge/Maturity-Sandbox-F9D71C)
![GitHub Release](https://img.shields.io/github/v/release/cemc-oper/cedar-graph)
![PyPI - Version](https://img.shields.io/pypi/v/cedar-graph)
![GitHub License](https://img.shields.io/github/license/cemc-oper/cedar-graph)
![GitHub Action Workflow Status](https://github.com/cemc-oper/cedar-graph/actions/workflows/ci.yaml/badge.svg)

`cedar-graph` 为 CEMC 数值预报产品提供数据请求、诊断计算和绘图产品定义，
支持 CMA-GFS、CMA-MESO、CMA-TYM 和 CMA-GEPS 等来源。它基于 `reki`、
`cedarkit-comp` 与 `cedarkit-plots`：产品通过单一 workflow 编译字段请求，
执行后创建 `Panel`/`Chart`/`PlotLayer`，最终使用 `cedarkit-plots` 渲染。

本项目处于 Sandbox 阶段，产品、recipe 和公共 API 仍可能演进。当前产品不保留
旧 `load_data`/`plot` adapter 或旧引擎执行链。

## 安装与开发

```bash
pip install cedar-graph

cd repo/cedar-graph
uv sync --extra test
MPLBACKEND=Agg uv run pytest tests/mock
```

读取真实 GRIB2 需要匹配的 ecCodes 库和 reki 数据源配置。合成数据示例不需要
业务文件或 CMADaaS 服务；安装与配置见
[`docs/getting_started/install.md`](docs/getting_started/install.md)。

## 快速绘图：读取 CMADaaS 挂载目录

`quick_plot()` 依据产品 ID 选择 workflow 产品，从 reki catalog 解析系统数据集，
并在本地挂载目录中查找文件。示例中的参数显式使用 pandas 时间值：

```python
import pandas as pd
from cedar_graph.quickplot import quick_plot

quick_plot(
    plot_type="cn.t2m",
    system_name="CMA-GFS",
    start_time=pd.Timestamp("2026-09-22 00:00:00"),
    forecast_time=pd.Timedelta("24h"),
    data_class="cmadaas",
    storage_base="/CMADAAS",
)
```

这是通过本地文件访问 CMADaaS 挂载目录，不会连接 CMADaaS 在线服务，也不需要
该服务的凭据。目录布局必须符合 reki 对所选系统的路径模板。`quick_plot()` 会
显示产品图，并在显示结束后关闭它所创建的 Panel/provider。

## 使用合成 provider 执行产品

所有内置 CEMC 图种和已迁移的诊断图产品都编译到 `cedarkit.plots/v3` workflow。
`MockDataSource` 实现相同的 provider 接口，使用固定解析式字段运行同一产品链：

```python
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.plan import CompileContext

product = select_workflow_product("cn.t2m")
context = CompileContext(
    start_time="2024-07-01",
    forecast_time="24h",
    params={"style_variant": "cn_summer"},
)
panel = product.run(MockDataSource(resolution=2), context)
try:
    panel.save("cn-t2m-mock.png")
finally:
    panel.close()
```

workflow 编译计划不含数据源路径或凭据。单位准备和诊断计算由 workflow 数据节点
完成，展示则交由 plots 的新内容模型；模板切换和重复渲染不会重新执行数据读取。
集合产品 `cn.ens_t2m` 由调用方提供实际成员 ID，MAX 输入及缺测策略显式配置。

## 产品和文档

内置产品涵盖地面场、高空形势、降水、对流诊断、风切变和集合温度。主要产品 ID
包括 `cn.t2m`、`cn.wind_10m`、`cn.h_500_psl`、`cn.rain_24h`、
`cn.cape_wind`、`cn.shr.default` 与 `cn.ens_t2m`。完整列表与合成输出见
[`docs/gallery/index.md`](docs/gallery/index.md)。

- [快绘与挂载目录](docs/tutorials/quick_plot.md)
- [显式 provider 与产品运行](docs/tutorials/manual_plot.md)
- [固定合成数据](docs/tutorials/mock_data.md)
- [v3 workflow recipe 与插件](docs/tutorials/recipe.md)
- [公开 workflow API](docs/api/index.md)
- [变更记录](docs/changelog.md)

代表产品页中的 cn.t2m 和 cn.ens_t2m 图像由 MyST-NB 在 Sphinx 构建时动态生成并
随 HTML 站点作为构建产物输出。固定日期、成员、DejaVu Sans 和 mock 分辨率下的独立 PNG 导出脚本可由
[`docs/examples/render_mock_products.py`](docs/examples/render_mock_products.py)
运行；默认输出到仓库外的临时目录：

```bash
uv sync --extra test
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/cedar-graph-docs-mpl \
  uv run python docs/examples/render_mock_products.py /tmp/cedar-graph-docs
```

## 许可

版权所有 &copy; 2021-2026, cemc-oper 开发者。本项目采用
[Apache License 2.0](LICENSE)。
