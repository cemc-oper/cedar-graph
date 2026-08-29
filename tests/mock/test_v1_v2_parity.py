"""Auditable data and image parity for all Python-to-recipe migrations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .image_baseline import image_metrics, save_difference_image
from .v1_v2_parity import PRODUCTS, assert_data_parity, historical_sha, load_v1_v2


# Historical modules and v2 recipes have identical data, styles and contour
# levels.  Matplotlib's automatic ``clabel`` placement nevertheless moves
# text/its opaque label background between the two artist construction orders.
# Keep that rendering-only tolerance separate from the normal PNG baseline
# tolerance (0.02) and require numeric parity independently above.
V1_V2_IMAGE_RMS_TOLERANCE = 0.05


@pytest.mark.parametrize("plot_name", PRODUCTS)
def test_v1_v2_final_data(plot_name, mock_data_source, start_time, forecast_time):
    """Every final v2 binding is identical to its deleted v1 implementation."""
    _, legacy, _, current = load_v1_v2(plot_name, mock_data_source, start_time, forecast_time)
    assert_data_parity(plot_name, legacy, current)


@pytest.mark.parametrize("plot_name", PRODUCTS)
def test_v1_v2_rendered_image(plot_name, mock_data_source, start_time, forecast_time, system_name, sample_step, tmp_path):
    """The legacy module and the v2 recipe render within the frozen RMS tolerance."""
    legacy_module, legacy, recipe_module, current = load_v1_v2(plot_name, mock_data_source, start_time, forecast_time)
    params = PRODUCTS[plot_name]["params"]
    legacy_metadata = legacy_module.PlotMetadata(
        start_time=start_time, forecast_time=forecast_time, system_name=system_name,
        sample_step=sample_step, **params,
    )
    current_metadata = recipe_module.PlotMetadata(
        start_time=start_time, forecast_time=forecast_time, system_name=system_name,
        sample_step=sample_step, **params,
    )
    legacy_path = Path(tmp_path, f"{plot_name}-v1.png")
    current_path = Path(tmp_path, f"{plot_name}-v2.png")
    legacy_module.plot(legacy, legacy_metadata).save(legacy_path)
    recipe_module.plot(current, current_metadata).save(current_path)
    metrics = image_metrics(current_path, legacy_path)
    difference_path = Path(tmp_path, f"{plot_name}-v1-v2-diff.png")
    save_difference_image(current_path, legacy_path, difference_path)
    evidence = {
        "historical_revision": historical_sha(),
        "plot": plot_name,
        **metrics,
        "tolerance": V1_V2_IMAGE_RMS_TOLERANCE,
        "difference_image": str(difference_path),
    }
    Path(tmp_path, f"{plot_name}-image-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(evidence, sort_keys=True))
    assert metrics["rms"] <= V1_V2_IMAGE_RMS_TOLERANCE, evidence
