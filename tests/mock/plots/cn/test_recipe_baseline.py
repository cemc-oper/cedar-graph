"""
配方（recipe）与 Python 模块共用 PNG 基线的对比测试。

渲染走 PlotEngine 配方流水线（MockDataSource 数据、与
``test_image_baseline.py`` 相同的元数据），对比对象为该文件生成的
基线 PNG。基线不入库：CI 环境或基线缺失时自动 skip。

覆盖全部 13 个可声明图形（设计文档 §4.5 转换清单）；shr、t_dew_t 等
诊断复杂图形保留 Python 逃生舱，不在此列。
"""
import os
from pathlib import Path

import pandas as pd
import pytest

from cedar_graph.data import DataLoader
from cedar_graph.recipes.engine import get_recipe_engine

from ...image_baseline import assert_image_match

IN_CI = os.environ.get("CI", "").lower() in ("true", "1", "yes")


def _render_recipe(recipe_name, mock_data_source, start_time, forecast_time, system_name, sample_step, output_path, **params):
    engine = get_recipe_engine()
    recipe_path = Path(__file__).parents[4] / "cedar_graph" / "recipes" / "cn" / f"{recipe_name}.yaml"
    module = engine.build_module(engine.load_recipe(recipe_path))

    data_loader = DataLoader(data_source=mock_data_source)
    plot_data = module.load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        **params,
    )
    metadata = module.PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        sample_step=sample_step,
        **params,
    )
    panel = module.plot(plot_data=plot_data, plot_metadata=metadata)
    panel.save(output_path)


#: recipe name -> (baseline name, extra params)
RECIPE_PLOTS = {
    "t2m": ("t_2m", {}),
    "h_500_psl": ("height_500_mslp", {}),
    "kidx_wind": ("k_wind", {"wind_level": 850.0}),
    "rh2m": ("rh_2m", {}),
    "cdbz": ("radar_reflectivity", {}),
    "h_500_wind_850": ("height_500_wind_850", {}),
    "bli_wind": ("bli_wind", {"wind_level": 850.0}),
    "cape_wind": ("cape_wind", {"wind_level": 850.0}),
    "cin_wind": ("cin_wind", {"wind_level": 850.0}),
    "wind_10m": ("wind_10m", {}),
    "rain_24h": ("rain_24h", {}),
    "rain_wind_10m": ("rain_wind_10m", {"interval": pd.Timedelta(hours=24)}),
    "prep_24h": ("prep_24h", {}),
}


@pytest.mark.parametrize("recipe_name", list(RECIPE_PLOTS.keys()))
def test_recipe_baseline(
        recipe_name,
        mock_data_source,
        start_time,
        forecast_time,
        system_name,
        sample_step,
        baseline_dir,
        tmp_path,
):
    """渲染配方并与对应 Python 模块的 PNG 基线对比（本地）。"""
    baseline_name, params = RECIPE_PLOTS[recipe_name]
    baseline_path = Path(baseline_dir, "cn", f"{baseline_name}.png")

    if IN_CI:
        pytest.skip("image baseline comparison runs locally only (baselines not committed)")
    if not baseline_path.exists():
        pytest.skip(
            f"baseline not found: {baseline_path}; "
            f"run pytest tests/mock --update-baseline to generate it locally"
        )

    render_path = Path(tmp_path, f"{recipe_name}.png")
    _render_recipe(
        recipe_name,
        mock_data_source=mock_data_source,
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        sample_step=sample_step,
        output_path=render_path,
        **params,
    )
    assert render_path.exists()
    assert_image_match(render_path, baseline_path)
