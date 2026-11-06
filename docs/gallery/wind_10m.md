---
mystnb:
  execution_mode: 'off'
---

# 10 m 风场（`cn.wind_10m`）

此产品通过 `cedarkit.plots/v3` workflow 选择数据请求、单位准备、样式和逻辑绘图内容。

查询使用已审核的 `cedarkit.u10m`／`cedarkit.v10m` 及等价的离地 10 m 条件。
u、v 和风速字段始终保留物理单位 m/s，风速由原始分量计算为
`sqrt(u² + v²)`，不在数据链中乘入风羽显示倍率。缺测按分量掩码传播，
实际起报、有效时间、预报时效和模式文字保留在图题中。

本产品单独选择 `cemc.wind:cn_mps`：半羽 2 m/s、整羽 4 m/s、旗标 20 m/s，
图题同时列出该编码。增量由样式传给绘图层的
[`barb_increments`](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.barbs.html)，
物理字段不转换成节或其他显示量。已有 `cemc.wind:cn` 和其他风产品不随本图更改。

本图以输入网格全域 20,000 个向量作为抽样预算，不是东亚视窗内的数量；
原 900 上限用于全球 1440×2880 网格时，东亚只留下几十个风羽。
当前冻结网格按步长 15 抽样为全球 18,432 个，东亚主图约 800 个，
保持原始风分量不变。其他分辨率按同一全域预算重新抽样。

使用固定日期 `2024-07-01 00 UTC`、24 小时时效和 `MockDataSource(resolution=2)` 可在本地重新渲染：

```bash
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/cedar-graph-docs-mpl \
  uv run python docs/examples/render_mock_products.py /tmp/cedar-graph-docs --plot cn.wind_10m
```

mock 字段用于复现流程与图层组合，不代表真实预报产品数值。真实数据绘图使用
[快绘入口](../tutorials/quick_plot.md) 或传入 `RekiProvider`，不修改产品 recipe。
