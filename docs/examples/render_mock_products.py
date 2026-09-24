"""将固定合成数据的产品图可选导出为 PNG。文档构建会动态内嵌代表图。"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import pandas as pd

from cedar_graph.recipes.ensemble_product import EnsembleRequest, EnsembleT2MProduct, select_ensemble_product
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedar_graph.testing import MockDataSource
from cedarkit.plots.workflow.plan import CompileContext


_DEFAULT_PARAMS = {
    "cn.bli_wind": {"wind_level": 850},
    "cn.cape_wind": {"wind_level": 850},
    "cn.cin_wind": {"wind_level": 850},
    "cn.div_wind.default": {"div_level": 850, "wind_level": 850},
    "cn.kidx_wind": {"wind_level": 850},
    "cn.pte_wind.default": {"wind_level": 850},
    "cn.qv_div.default": {"level": 850},
    "cn.rain_wind_10m": {"interval": "3h"},
    "cn.shr.default": {"first_level": 3000, "second_level": 0},
    "cn.t2m": {"style_variant": "cn_summer"},
    "cn.t_dew_t.default": {"level": 850},
}


def _render_workflow(name: str, output: Path) -> dict[str, object]:
    product = select_workflow_product(name)
    if product is None:
        raise ValueError(f"unknown workflow product: {name}")
    context = CompileContext(
        start_time="2024-07-01T00:00:00",
        forecast_time="24h",
        params=_DEFAULT_PARAMS.get(name, {}),
    )
    source = MockDataSource(resolution=2)
    panel = product.run(source, context)
    try:
        panel.save(output)
    finally:
        panel.close()
    return {
        "product": name,
        "output": str(output.resolve()),
        "bytes": output.stat().st_size,
        "provider_requests": len(source.workflow_requests),
    }


def _render_ensemble(output: Path) -> dict[str, object]:
    product = select_ensemble_product("cn.ens_t2m")
    if not isinstance(product, EnsembleT2MProduct):
        raise RuntimeError("cn.ens_t2m product is unavailable")
    request = EnsembleRequest(
        member_ids=("m001", "m002"),
        control_id="m000",
        include_control_in_max=True,
        missing_policy="error",
        columns=3,
    )
    source = MockDataSource(resolution=3)
    prepared = product.prepare(
        source,
        start_time=pd.Timestamp("2024-07-01T00:00:00"),
        forecast_time=pd.Timedelta("24h"),
        request=request,
    )
    panel = prepared.render()
    chart_ids = list(panel.charts)
    try:
        panel.save(output)
    finally:
        panel.close()
    return {
        "product": "cn.ens_t2m",
        "output": str(output.resolve()),
        "bytes": output.stat().st_size,
        "charts": chart_ids,
        "max_input_ids": list(prepared.max_input_ids),
        "provider_requests": len(source.workflow_requests),
    }


def render(output_dir: Path, *, plot: str | None = None) -> list[dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    mpl.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "figure.dpi": 100,
        "savefig.dpi": 120,
    })
    if plot == "cn.ens_t2m":
        return [_render_ensemble(output_dir / "cn-ens-t2m-mock.png")]
    if plot is not None:
        return [_render_workflow(plot, output_dir / f"{plot.replace('.', '-')}-mock.png")]
    return [
        _render_workflow("cn.t2m", output_dir / "cn-t2m-mock.png"),
        _render_ensemble(output_dir / "cn-ens-t2m-mock.png"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_dir", type=Path, nargs="?", default=Path("/tmp/cedar-graph-docs"),
        help="独立 PNG 输出目录（默认：/tmp/cedar-graph-docs）",
    )
    parser.add_argument("--plot", help="产品 ID；省略时绘制 cn.t2m 与 cn.ens_t2m")
    args = parser.parse_args()
    for item in render(args.output_dir, plot=args.plot):
        print(item)


if __name__ == "__main__":
    main()
