"""AST guard: cedar-graph must not depend on its task application."""

import ast
from pathlib import Path

import cedar_graph


PACKAGE_DIR = Path(cedar_graph.__file__).parent


def test_cedar_graph_does_not_import_cemc_plots_kit():
    offenders = []
    for path in PACKAGE_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            else:
                continue
            if any(name == "cemc_plots_kit" or name.startswith("cemc_plots_kit.") for name in names):
                offenders.append(f"{path.relative_to(PACKAGE_DIR)}:{node.lineno} imports cemc_plots_kit")
    assert not offenders, (
        "cedar-graph is below cemc-plots-kit in the runtime dependency "
        "graph and must not import it:\n" + "\n".join(offenders)
    )
