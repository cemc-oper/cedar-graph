"""CEMC plot recipes (YAML).

Recipes under ``cn/`` are loaded by the quick_plot loader before Python
plot modules (``cedar_graph.plots``); both expose the same interface.
See ``cedar_graph.recipes.engine`` for the configured ``PlotEngine``
(field registry + diagnostic ops) used to execute them.
"""

from pathlib import Path

#: recipe search directories, cn first.
RECIPE_PATHS = [Path(__file__).parent / "cn"]
