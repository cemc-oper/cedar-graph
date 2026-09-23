"""CEMC plot recipes (YAML).

Recipes under ``workflow/cn/`` are discovered as v3 workflow products.
The public product IDs remain ``cn.*``.
(field registry + diagnostic ops) used to execute them.
"""

from pathlib import Path

#: recipe search directories, cn first.
RECIPE_PATHS = [Path(__file__).parent / "cn"]
