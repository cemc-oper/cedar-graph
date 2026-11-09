---
mystnb:
  execution_mode: 'off'
---

# 24 小时累计降水（`cn.rain_24h`）

此产品通过 `cedarkit.plots/v3` workflow 选择数据请求、单位准备、样式和逻辑绘图内容。

使用固定日期 `2024-07-01 00 UTC`、24 小时时效和 `MockDataSource(resolution=2)` 可在本地重新渲染：

```bash
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/cedar-graph-docs-mpl \
  uv run python docs/examples/render_mock_products.py /tmp/cedar-graph-docs --plot cn.rain_24h
```

mock 字段用于复现流程与图层组合，不代表真实预报产品数值。真实数据绘图使用
[快绘入口](../tutorials/quick_plot.md) 或传入 `RekiProvider`，不修改产品 recipe。

## Reviewed GFS original-data batch

N09C qualifies CMA-GFS ORIG initialized at 2026-11-02 12 UTC for the 0–24h and
24–48h windows. `cn.rain_24h` selects `cedarkit.rain.since-initialization` at both
endpoints and enables the guarded `time_diff` accumulation contract. The original
0h endpoint is an encoded initialization zero; the product is unavailable before
24h and never substitutes a missing prior endpoint with zero.

Both endpoints must share the reference, parameter, vertical/member identity and
spatial grid, with cumulative intervals beginning at initialization and ending at
the requested times. Resets or inconsistent clocks fail. Values remain in mm;
GRIB kg/m2 and the reviewed precipitation mm interpretation preserve the numbers.

Decoded endpoints can produce small negative differences at different packing
resolutions. This batch retains and counts those differences within the sum of
the two half-quantization steps, derived from lossless GRIB packing metadata;
larger decreases fail. There is no clipping, guessed scale or reset recovery.
This bound describes encoded precision and does not establish the original
model's exact precipitation or prove that every small decrease has that cause.

The derived field records `accumulation_start`, `accumulation_end`,
`accumulation_hours`, `negative_difference_bound` and `negative_difference_points`,
plus both source identities, references and query reports. It does not retain one
endpoint's since-initialization identity or report as if it described the derived
24-hour amount. Titles show the model, initialization, valid time and exact
forecast-hour window; the colorbar is mm.

```yaml
api_version: cemc.plots/v2
kind: PlotTask
source:
  dataset: cma_gfs_gmf_cmadaas_mount
  overrides:
    storage_base: /CMADAAS
time:
  start_time: '2026110212'
  forecast_start: 24h
  forecast_time: 48h
  forecast_interval: 24h
runtime:
  output_dir: /tmp/gfs-rain-24h
  missing: fail
  workers: 1
  shared_reads: true
plots:
  cn.rain_24h:
    model: CMA-GFS
```

The public input reports remain unchecked where no independent expected domain
exists. The qualification covers these frozen originals and two product windows;
N10D separately verifies the final installed package/resource combination and
recovery. Controlled reset/decrease cases are failure fixtures, not observations
of actual production resets. The gallery's synthetic input is not scientific
acceptance evidence.
