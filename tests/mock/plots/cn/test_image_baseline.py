"""
配方图形的 PNG 基线对比测试。

基线 PNG 体积较大，不入库，仅用于本地开发期对照：
CI 环境（``CI`` 环境变量）或基线缺失时自动 skip；
本地加 ``--update-baseline`` 运行时生成/更新基线（存于
``tests/mock/baseline/cn/``，已被 gitignore）。

数据来自 ``cedar_graph.testing.MockDataSource``（确定性合成场），
渲染走 PlotEngine 配方流水线（Python 图形模块已随 G4 删除，
配方是唯一实现），渲染参数固定，本地可复现。

覆盖全部 13 个可声明图形（设计文档 §4.5 转换清单）；shr、t_dew_t 等
诊断复杂图形保留 Python 逃生舱（``cedar_graph.plots.cn``），由各自的
渲染冒烟测试覆盖，不在此列。
"""
import os
from pathlib import Path

import pandas as pd
import pytest

from cedar_graph.data import DataLoader
from cedar_graph.recipes.engine import get_recipe_engine

from ...image_baseline import assert_image_match

#: CI 环境标识（GitHub Actions 等主流 CI 均设置 CI=true）
IN_CI = os.environ.get("CI", "").lower() in ("true", "1", "yes")


def _render_recipe(recipe_name, params, mock_data_source, start_time, forecast_time, system_name, sample_step, output_path):
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


#: plot name -> (recipe name, extra load/plot params)
#: 覆盖全部 13 个可声明图形（配方转换清单，设计文档 §4.5）。
BASELINE_PLOTS = {
    "t_2m": ("t2m", {}),
    "height_500_mslp": ("h_500_psl", {}),
    "k_wind": ("kidx_wind", {"wind_level": 850.0}),
    "rh_2m": ("rh2m", {}),
    "radar_reflectivity": ("cdbz", {}),
    "height_500_wind_850": ("h_500_wind_850", {}),
    "bli_wind": ("bli_wind", {"wind_level": 850.0}),
    "cape_wind": ("cape_wind", {"wind_level": 850.0}),
    "cin_wind": ("cin_wind", {"wind_level": 850.0}),
    "wind_10m": ("wind_10m", {}),
    "rain_24h": ("rain_24h", {}),
    "rain_wind_10m": ("rain_wind_10m", {"interval": pd.Timedelta(hours=24)}),
    "prep_24h": ("prep_24h", {}),
}


@pytest.mark.parametrize("plot_name", list(BASELINE_PLOTS.keys()))
def test_image_baseline(
        plot_name,
        mock_data_source,
        start_time,
        forecast_time,
        system_name,
        sample_step,
        baseline_dir,
        update_baseline,
        tmp_path,
):
    """渲染配方图形并与 PNG 基线对比（本地）或重新生成基线。"""
    baseline_path = Path(baseline_dir, "cn", f"{plot_name}.png")

    if update_baseline:
        baseline_path.parent.mkdir(exist_ok=True, parents=True)
        render_path = baseline_path
    else:
        if IN_CI:
            pytest.skip("image baseline comparison runs locally only (baselines not committed)")
        if not baseline_path.exists():
            pytest.skip(
                f"baseline not found: {baseline_path}; "
                f"run pytest with --update-baseline to generate it locally"
            )
        render_path = Path(tmp_path, f"{plot_name}.png")

    recipe_name, params = BASELINE_PLOTS[plot_name]
    _render_recipe(
        recipe_name,
        params,
        mock_data_source=mock_data_source,
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        sample_step=sample_step,
        output_path=render_path,
    )
    assert render_path.exists()

    if update_baseline:
        # 生成模式下自检：基线必须与自身完全一致
        assert_image_match(render_path, baseline_path, tolerance=0.0)
    else:
        assert_image_match(render_path, baseline_path)
