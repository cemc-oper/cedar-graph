---
mystnb:
  execution_mode: 'off'
---

# workflow 配方

cedar-graph 产品遵循 `cedarkit.plots/v3` workflow schema。旧 recipe schema、旧
`load_data`/`plot` adapter 和并行执行引擎已删除；新产品使用
`cedar_graph.recipes.workflow_product` 的选择入口。

## 内置产品

```python
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.plan import CompileContext

product = select_workflow_product("cn.rain_24h")
context = CompileContext(start_time="2024-07-01", forecast_time="24h")
plan = product.compile(context)
print(plan.summary())

panel = product.run(MockDataSource(resolution=2), context)
try:
    panel.save("rain-24h.png")
finally:
    panel.close()
```

产品编译得到 source-neutral 计划，执行时才接入 provider。`MockDataSource` 用于
确定性检查；真实数据通过 `RekiProvider` 提供。

## 外部 v3 配方与 CLI

自定义 recipe 的字段请求、单位准备、算子、逻辑绘图内容和展示配置按
`cedarkit.plots/v3` schema 声明。运行前可用底层 plots CLI 做静态校验和计划预览：

```bash
cedarkit-plots recipe validate path/to/recipe.yaml
cedarkit-plots recipe plan path/to/recipe.yaml \
  --start-time 2024-07-01T00:00Z --forecast-time 24h --format json
```

校验和 plan 不读取字段、不调用 provider、不渲染。app 任务文件则使用独立的
`cemc.plots/v2` task schema，并可将外部 `cedarkit.plots/v3` YAML 路径作为一个
产品；两个版本对应不同的文档类型。schema 的完整说明见
cedarkit-plots 的 [v3 recipe 教程](https://github.com/cemc-oper/cedarkit-plots/blob/main/docs/tutorials/recipe_v3.md)。

插件写法见 {doc}`workflow_plugins`。
