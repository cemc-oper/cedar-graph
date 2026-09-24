---
mystnb:
  execution_mode: 'off'
---

# 核心概念

cedar-graph 选择版本化 workflow 产品，将其编译为字段请求，经 provider 执行，最后
渲染为 `cedarkit.plots.Panel`。

## 产品与 provider

内置产品使用 v3 workflow recipe 和注册算子。`RekiProvider` 将 `reki.SourceSpec`
适配为 workflow 字段读取接口；`MockDataSource` 实现相同协议并生成固定合成字段，
因此产品不需要挂载业务数据也能运行。

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
    panel.show()
finally:
    panel.close()
```

真实 GRIB2 运行时从 reki catalog 解析数据源后传给 `RekiProvider`。
`quick_plot()` 根据产品的 `system_name` 执行便捷 catalog 解析，示例见
{doc}`../tutorials/quick_plot`。

## workflow recipe 与绘图内容

recipe 声明字段请求、注册算子、样式、逻辑绘图内容和展示配置。
`WorkflowProduct.compile()` 返回 source-neutral 的 workflow 计划；
`WorkflowProduct.run()` 执行并渲染当前 `Panel` 内容模型。自定义 recipe 也使用
同一个 v3 schema，可由 app task runner 选择。schema 与静态检查见
{doc}`../tutorials/recipe`。
