"""Selection and execution of migrated v3 recipe products."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cedarkit.plots.workflow.discovery import discover_workflow
from cedarkit.plots.workflow.plan import CompileContext, WorkflowPlan, compile_recipe
from cedarkit.plots.workflow.recipe import LoadedRecipe, load_recipe
from cedarkit.plots.workflow.render import render_result


_MIGRATED = {f"cn.{name}": f"cn.{name}" for name in (
    "bli_wind", "cape_wind", "cdbz", "cin_wind", "h_500_psl", "h_500_wind_850",
    "kidx_wind", "prep_24h", "rain_24h", "rain_wind_10m", "rh2m", "t2m", "wind_10m",
)}
_MIGRATED.update({f"cn.{name}.default": f"cn.{name}" for name in (
    "div_wind", "pte_wind", "qv_div", "shr", "t_dew_t",
)})


@dataclass(frozen=True)
class WorkflowProduct:
    name: str
    recipe: LoadedRecipe
    discovery: Any

    def compile(self, context: CompileContext) -> WorkflowPlan:
        return compile_recipe(self.recipe, context, registry=self.discovery.ops)

    def run(self, provider: Any, context: CompileContext):
        plan = self.compile(context)
        result = plan.execute(provider, registry=self.discovery.ops)
        return render_result(result, domains=self.discovery.domains)


def select_workflow_product(name: str) -> WorkflowProduct | None:
    """Return a v3 product only after its migrated resource is available."""
    recipe_id = _MIGRATED.get(name)
    if recipe_id is None:
        return None
    discovered = discover_workflow()
    return WorkflowProduct(name, discovered.recipes.load(recipe_id), discovered)


def load_workflow_product(path) -> WorkflowProduct:
    """Load a caller-supplied v3 recipe with the same runtime as built-ins."""
    discovered = discover_workflow()
    return WorkflowProduct(str(path), load_recipe(path), discovered)
