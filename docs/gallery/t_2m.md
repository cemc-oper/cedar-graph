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

# 2 m 温度（`cn.t2m`）

此产品通过 `cedarkit.plots/v3` workflow 选择数据请求、单位准备、样式和逻辑绘图内容。
固定使用暖季样式 `cn_summer`。下面使用固定日期、24 小时时效和
`MockDataSource(resolution=2)`，文档构建时执行并直接显示图像，不生成仓库内图片。

```{code-cell} python
%matplotlib inline
import matplotlib as mpl
from IPython.display import display
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.plan import CompileContext

mpl.rcParams["font.family"] = "DejaVu Sans"

product = select_workflow_product("cn.t2m")
assert product is not None
source = MockDataSource(resolution=2)
context = CompileContext(
    start_time="2024-07-01T00:00:00",
    forecast_time="24h",
    params={"style_variant": "cn_summer"},
)
panel = product.run(source, context)
try:
    print(f"provider requests: {len(source.workflow_requests)}")
    display(panel.render())
finally:
    panel.close()
```

mock 字段用于复现流程与图层组合，不代表真实预报产品数值。真实数据绘图使用
[快绘入口](../tutorials/quick_plot.md) 或传入 `RekiProvider`，不修改产品 recipe。
