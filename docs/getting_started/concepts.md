---
mystnb:
  execution_mode: 'off'
---

# Core concepts

cedar-graph selects a versioned workflow product, compiles it into field
requests, executes those requests through a provider, and renders the result
as a `cedarkit.plots.Panel`.

## Products and providers

Built-in products use workflow recipes and registered diagnostic operations.
`RekiProvider` adapts a `reki.SourceSpec` to the workflow field-request
contract. `MockDataSource` implements the same contract with deterministic
synthetic fields, so a product can run without mounted operational data.

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

For mounted GRIB2 data, resolve a dataset from the reki catalog and pass its
`SourceSpec` to `RekiProvider`. The convenience `quick_plot` function performs
that catalog resolution from the selected system name.

## Workflow recipes

A recipe declares field requests, registered operations, styles, and display
content. `WorkflowProduct.compile()` returns a source-neutral plan;
`WorkflowProduct.run()` executes and renders it. Custom recipe files use the
same v3 schema and can be selected by the app task runner. See
{doc}`../tutorials/recipe_v3` for the current recipe format.
