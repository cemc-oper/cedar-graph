---
mystnb:
  execution_mode: 'off'
---

# Workflow products

Built-in graph products compile versioned workflow recipes into field
requests, execute them through a provider, then render a caller-owned Panel.
Diagnostic calculations are registered as workflow operations; they do not
provide a parallel `load_data`/`plot` product API.

```{eval-rst}
.. automodule:: cedar_graph.recipes.workflow_product
   :members:
   :undoc-members:
   :show-inheritance:
```

## Collection products

```{eval-rst}
.. automodule:: cedar_graph.recipes.ensemble_product
   :members:
   :undoc-members:
   :show-inheritance:
```
