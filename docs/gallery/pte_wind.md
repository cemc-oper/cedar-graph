---
mystnb:
  execution_mode: 'off'
---

# 假相当位温与风场（`cn.pte_wind.default`）

此产品通过 `cedarkit.plots/v3` workflow 选择数据请求、单位准备、样式和逻辑绘图内容。 使用迁移后的 workflow 诊断产品。

使用固定日期 `2024-07-01 00 UTC`、24 小时时效和 `MockDataSource(resolution=2)` 可在本地重新渲染：

```bash
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/cedar-graph-docs-mpl \
  uv run python docs/examples/render_mock_products.py /tmp/cedar-graph-docs --plot cn.pte_wind.default
```

mock 字段用于复现流程与图层组合，不代表真实预报产品数值。真实数据绘图使用
[快绘入口](../tutorials/quick_plot.md) 或传入 `RekiProvider`，不修改产品 recipe。
