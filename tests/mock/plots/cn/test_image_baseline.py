"""
试点及批量转换图形的 PNG 基线对比测试。

基线 PNG 体积较大，不入库，仅用于本地开发期对照：
CI 环境（``CI`` 环境变量）或基线缺失时自动 skip；
本地加 ``--update-baseline`` 运行时生成/更新基线（存于
``tests/mock/baseline/cn/``，已被 gitignore）。

数据来自 ``cedar_graph.testing.MockDataSource``（确定性合成场），
渲染参数固定，本地可复现。基线由 Python 图形模块渲染生成，
``test_recipe_baseline.py`` 用同一批基线验收配方版本。
"""
import importlib
import os
from pathlib import Path

import pandas as pd
import pytest

from cedar_graph.data import DataLoader

from ...image_baseline import assert_image_match

#: CI 环境标识（GitHub Actions 等主流 CI 均设置 CI=true）
IN_CI = os.environ.get("CI", "").lower() in ("true", "1", "yes")


def _render_module(module_path, params, mock_data_source, start_time, forecast_time, system_name, sample_step, output_path):
    plot_module = importlib.import_module(f"cedar_graph.plots.cn.{module_path}.default")

    data_loader = DataLoader(data_source=mock_data_source)
    plot_data = plot_module.load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        **params,
    )
    metadata = plot_module.PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        sample_step=sample_step,
        **params,
    )
    panel = plot_module.plot(plot_data=plot_data, plot_metadata=metadata)
    panel.save(output_path)


#: plot name -> (module path, extra load/plot params)
#: 覆盖全部 13 个可声明图形（配方转换清单，设计文档 §4.5）。
BASELINE_PLOTS = {
    "t_2m": ("t_2m", {}),
    "height_500_mslp": ("height_500_mslp", {}),
    "k_wind": ("k_wind", {"wind_level": 850.0}),
    "rh_2m": ("rh_2m", {}),
    "radar_reflectivity": ("radar_reflectivity", {}),
    "height_500_wind_850": ("height_500_wind_850", {}),
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
    """渲染图形并与 PNG 基线对比（本地）或重新生成基线。"""
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

    module_path, params = BASELINE_PLOTS[plot_name]
    _render_module(
        module_path,
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
