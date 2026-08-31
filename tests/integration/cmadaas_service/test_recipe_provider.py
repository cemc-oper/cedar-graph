"""Real MUSIC evidence for the Recipe v2 provider path.

This test is deliberately outside cedar-graph's default mock test path.  It
uses the runtime CMADaaS credential configuration and a small Beijing region;
neither credentials nor the region are persisted in the Recipe or PlotPlan.
"""
from pathlib import Path

import pandas as pd
import pytest

import reki
from cedar_graph.data import RekiProvider
from cedarkit.plots.plan import CompileContext, compile_recipe
from cedarkit.plots.recipe import load_recipe


pytestmark = pytest.mark.cmadaas_service

REGION = {
    "type": "rect",
    "start_latitude": 39,
    "end_latitude": 41,
    "start_longitude": 115,
    "end_longitude": 117,
}

# Verified through MUSIC during the stage-5 acceptance run.  Keep this fixed
# sample separate from the rolling health smoke in reki's service tests.
FIXED_START_TIME = pd.Timestamp("2026-08-30T00:00:00Z")


def test_t2m_recipe_v2_loads_through_cmadaas_provider():
    if not Path("~/.config/cedarkit.yaml").expanduser().exists():
        pytest.skip("CMADaaS config ~/.config/cedarkit.yaml not found")

    recipe_path = Path(__file__).parents[3] / "cedar_graph" / "recipes" / "cn" / "t2m.yaml"
    plan = compile_recipe(
        load_recipe(recipe_path),
        CompileContext(
            start_time=FIXED_START_TIME,
            forecast_time="24h",
        ),
    )
    provider = RekiProvider(
        reki.load_catalog(plugins=False, user=False).resolve("CMA-GFS-CMADaaS"),
        region=REGION,
    )

    value = plan.execute(provider).outputs["t2m"]

    assert value.name == "cedarkit.t2m"
    assert value.attrs["units"] == "degC"
    assert value.attrs["cmadaas_parameter"] == "TEM"
    assert value.sizes["latitude"] > 1
    assert value.sizes["longitude"] > 1
    assert provider.trace[-1].dataset_id == "cma_gfs_gmf_cmadaas"
    assert provider.trace[-1].external_parameter == "TEM"
    assert "region" not in plan.to_json()
