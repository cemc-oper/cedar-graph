---
mystnb:
  execution_mode: 'off'
---

# Recipe guide

cedar-graph products use the v3 workflow recipe schema. Earlier recipe formats
and the `load_data`/`plot` adapter have been removed. For the current schema,
field requests, operations, display declarations, and a runnable product
example, see {doc}`recipe_v3`.

Use `select_workflow_product()` for a built-in product or
`load_workflow_product()` for a caller-supplied v3 recipe file. Both compile to
the same source-neutral workflow plan and render through the current Panel API.
