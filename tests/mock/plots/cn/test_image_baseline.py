"""
试点图形（t_2m、height_500_mslp、k_wind）的 PNG 基线对比测试。

基线 PNG 体积较大，不入库，仅用于本地开发期对照：
CI 环境（``CI`` 环境变量）或基线缺失时自动 skip；
本地加 ``--update-baseline`` 运行时生成/更新基线（存于
``tests/mock/baseline/cn/``，已被 gitignore）。

数据来自 ``cedar_graph.testing.MockDataSource``（确定性合成场），
渲染参数固定，本地可复现。
"""
import os
from pathlib import Path

import pytest

from cedar_graph.data import DataLoader

from ...image_baseline import assert_image_match

#: CI 环境标识（GitHub Actions 等主流 CI 均设置 CI=true）
IN_CI = os.environ.get("CI", "").lower() in ("true", "1", "yes")


def _render_t_2m(mock_data_source, start_time, forecast_time, system_name, sample_step, output_path):
    from cedar_graph.plots.cn.t_2m.default import PlotMetadata, plot, load_data

    data_loader = DataLoader(data_source=mock_data_source)
    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        sample_step=sample_step,
    )
    panel = plot(plot_data=plot_data, plot_metadata=metadata)
    panel.save(output_path)


def _render_height_500_mslp(mock_data_source, start_time, forecast_time, system_name, sample_step, output_path):
    from cedar_graph.plots.cn.height_500_mslp.default import PlotMetadata, plot, load_data

    data_loader = DataLoader(data_source=mock_data_source)
    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        sample_step=sample_step,
    )
    panel = plot(plot_data=plot_data, plot_metadata=metadata)
    panel.save(output_path)


def _render_k_wind(mock_data_source, start_time, forecast_time, system_name, sample_step, output_path):
    from cedar_graph.plots.cn.k_wind.default import PlotMetadata, plot, load_data

    wind_level = 850.0
    data_loader = DataLoader(data_source=mock_data_source)
    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        wind_level=wind_level,
    )
    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        wind_level=wind_level,
        sample_step=sample_step,
    )
    panel = plot(plot_data=plot_data, plot_metadata=metadata)
    panel.save(output_path)


PILOT_PLOTS = {
    "t_2m": _render_t_2m,
    "height_500_mslp": _render_height_500_mslp,
    "k_wind": _render_k_wind,
}


@pytest.mark.parametrize("plot_name", list(PILOT_PLOTS.keys()))
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
    """渲染试点图形并与 PNG 基线对比（本地）或重新生成基线。"""
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

    PILOT_PLOTS[plot_name](
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
