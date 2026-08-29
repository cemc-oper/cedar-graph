---
mystnb:
  execution_mode: 'off'
---

# cedar-graph Recipe v2 与插件扩展

`cedar-graph` 发布的 13 个中国区域产品位于 `cedar_graph/recipes/cn/`，
均为 `cedarkit.plots/v2` 文档。它们由核心编译器生成 PlotPlan；业务包不应
绕过 compiler 或在运行时执行隐藏读取。Recipe v2 的完整 schema、迁移和
plan JSON 说明见 cedarkit-plots 的 Recipe v2 文档。

## 内置注册

包通过三个受控 entry point 暴露资源：

- `cedarkit.plots.recipes`：`recipe_provider()` 返回打包 recipe root；
- `cedarkit.plots.ops`：`op_descriptors()` 返回 `wind_speed` 与
  `prep_classify` 的 `OpDescriptor`；
- `cedarkit.plots.domains`：`domain_descriptors()` 返回 `east_asia` 与
  `cn_area` 模板描述符。

provider 只返回资源或描述符，导入不修改全局注册表。核心按稳定顺序发现插件，
重名 op 默认报错；安装 cedar-graph 后，以下预览可看到诊断 op、`time_diff`
新增的早时次请求和单位 conversion 节点：

```bash
cedarkit-plots recipe validate cedar_graph/recipes
cedarkit-plots recipe plan cedar_graph/recipes/cn/rain_24h.yaml \
  --start-time 2024-07-01T00:00Z --forecast-time 24h --format json
```

## 新增业务 recipe 或 op

新增 recipe 时先用稳定 parameter ID 和显式 `data.units` 表达科学数据；
style 的 expected units 仅校验。只有在需要新的、可复用的纯数据操作时才新增
`OpDescriptor`，明确输入/输出数量、pure/reusable 及版本化 contract。
需要额外请求的 op 使用 planner hook 描述 RequestKey 依赖，禁止在 callable
中访问 provider。

新增后至少运行目录 validate、plan JSON preview、mock 数值/图片对拍。若保留
Python v1 模块，必须说明其公开兼容原因，并与 v2 走同一规范化/编译主链路。
图片差异不能替代 DataArray 的 dims、coords、attrs、units、NaN mask 和数值
对拍。
