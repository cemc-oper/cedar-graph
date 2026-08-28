from pathlib import Path

import reki

from cedar_graph.recipes.engine import FIELD_INFOS, OVERRIDE_FIELDS, get_recipe_engine


def test_all_builtin_recipe_fields_are_parameter_ids_and_load():
    engine = get_recipe_engine()
    recipe_dir = Path(__file__).parents[2] / "cedar_graph" / "recipes" / "cn"
    recipes = [engine.load_recipe(path) for path in sorted(recipe_dir.glob("*.yaml"))]
    fields = {
        spec.field
        for recipe in recipes
        for spec in recipe.data.values()
        if spec.field is not None
    }
    assert len(recipes) == 13
    assert fields
    assert all(field.startswith("cedarkit.") for field in fields)
    assert not OVERRIDE_FIELDS


def test_legacy_field_view_and_parameter_ids_resolve_to_same_query():
    for legacy_name, legacy_info in FIELD_INFOS.items():
        parameter_id = legacy_info.parameter_id
        assert parameter_id is not None
        assert legacy_info.to_field_query() == reki.resolve_parameter(parameter_id).query
