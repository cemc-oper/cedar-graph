---
mystnb:
  execution_mode: 'off'
---

# 使用绘图样式

当前 CEMC 与通用要素样式由 `cedarkit-plots` 内置并随其发行。cedar-graph 的
workflow recipe 按产品需要显式选择样式 ID 和变体；graph 不再复制一套样式 YAML、
palette 或样式注册插件。

例如温度 recipe 使用 `cemc.t2m:cn_summer`，风场 recipe 使用
`cemc.wind:cn`。产品执行前，workflow 在数据节点完成单位准备；底层样式只校验
准备后数据的 units、temperature kind 与累计时段，不会隐式转换字段。

手动检查样式或绘制已准备字段时，可直接访问底层注册表：

```python
from cedar_graph.testing import MockDataSource
from cedarkit.plots.style import StyleRegistry

source = MockDataSource(resolution=2)
field = source.field(
    "cedarkit.t2m",
    start_time="2024-07-01",
    forecast_time="24h",
)
registry = StyleRegistry.default()
style = registry.get_style("cemc.t2m:cn_summer", data=field)
```

`generic.t` 属于显式通用 profile，不是 CEMC 自动匹配失败后的默认回退：

```python
generic = StyleRegistry.default(profile="generic")
generic_style = generic.get_style("t", data=field)
```

样式文件 schema、profile 优先级、palette 和自定义样式的完整说明见
[`cedarkit-plots/docs/tutorials/style_library.md`](https://github.com/cemc-oper/cedarkit-plots/blob/main/docs/tutorials/style_library.md)。
