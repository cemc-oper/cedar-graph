---
mystnb:
  execution_mode: 'off'
---

# 手动绘图

直接选择 v3 产品可检查静态计划，再用自定义 provider 执行。
下面用合成数据绘制 500 hPa 高度场与海平面气压。

```{code-cell} python
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.plan import CompileContext

product = select_workflow_product("cn.h_500_psl")
context = CompileContext(start_time="2024-07-01", forecast_time="24h")
plan = product.compile(context)
print(plan.summary())

panel = product.run(MockDataSource(resolution=2), context)
try:
    panel.show()
finally:
    panel.close()
```

生产环境可向 `product.run` 传入由 reki `SourceSpec` 构造的
{class}`cedar_graph.data.RekiProvider`。调用方负责关闭自行创建的 provider。
同一个选择与执行接口也适用于 `cn.shr.default` 等迁移后的诊断产品；
参数通过 `CompileContext(params=...)` 传入。
