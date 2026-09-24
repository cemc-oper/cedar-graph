---
mystnb:
  execution_mode: 'off'
---

# workflow 产品

内置 YAML 位于 `cedar_graph/recipes/workflow/cn/`，遵循
`cedarkit.plots/v3` schema。通过 `select_workflow_product()` 选择产品；外部
v3 recipe 使用相同的编译器和 provider 协议。参见
{doc}`../tutorials/recipe`。

```{eval-rst}
.. automodule:: cedar_graph.recipes.workflow_product
   :members:
   :undoc-members:
   :show-inheritance:
```

## 集合产品

`cn.ens_t2m` 的 `EnsembleT2MProduct` 依据真实请求成员准备数据与统计 MAX，之后
由返回对象创建 Chart 并渲染。`ens_cn` 模板只负责排列已有成员图表。

```{eval-rst}
.. automodule:: cedar_graph.recipes.ensemble_product
   :members:
   :undoc-members:
   :show-inheritance:
```
