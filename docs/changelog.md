---
mystnb:
  execution_mode: 'off'
---

# 变更记录

权威的变更日志在 [GitHub Releases](https://github.com/cemc-oper/cedar-graph/releases)
中维护。重要变更会同步在这里。

## 待发布

- `RekiProvider` 现按 source capability 分派 CMADaaS direct-result 请求：在
  source 创建前绑定稳定 parameter ID、FieldQuery 和时次，不对内存结果调用
  `.sel()`。Recipe/PlotPlan 保持 source-neutral，`check_many()` 对无
  metadata-only 能力的服务返回 `unknown`。
- 内置 CEMC recipe 已发布为 Recipe v2 资源，并通过受控的 recipe/op/domain
  entry point 接入。历史 Python 模块保留为公开 v1 兼容表面，供调用方迁移。
- 新增 ReadTheDocs 文档站点（Sphinx + sphinx-book-theme），
  绘图样例由 {class}`cedar_graph.testing.MockDataSource` 在构建时
  实时执行。
- 新增公开模块 `cedar_graph.testing`，与 mock 测试套件复用同一份合成数据源。
