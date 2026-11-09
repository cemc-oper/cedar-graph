---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# EnsCN 2 m 温度（`cn.ens_t2m`）

集合产品显式声明实际扰动成员 ID、可选 control、MAX 输入成员、缺测策略和列数。
本固定 mock 样例使用 `m000` control 与 `m001`、`m002` 成员，并让 control 参与
MAX。统计场在数据阶段从存在的输入逐点计算，模板只排列生成后的 Chart。文档构建时
运行以下单元格并直接显示生成的图像，不保存仓库内静态图片。

```{code-cell} python
%matplotlib inline
import matplotlib as mpl
import pandas as pd
from IPython.display import display
from cedar_graph.recipes.ensemble_product import (
    EnsembleRequest,
    EnsembleT2MProduct,
    select_ensemble_product,
)
from cedar_graph.testing import MockDataSource

mpl.rcParams["font.family"] = "DejaVu Sans"

product = select_ensemble_product("cn.ens_t2m")
assert isinstance(product, EnsembleT2MProduct)
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
try:
    print(f"charts: {tuple(panel.charts)}")
    print(f"MAX inputs: {prepared.max_input_ids}")
    print(f"provider requests: {len(source.workflow_requests)}")
    display(panel.render())
finally:
    panel.close()
```

该样例中的成员偏移是确定性测试数据，不代表业务集合预报。真实成员编号和缺测
规则应由具体数据源与任务配置确定。

## Reviewed GEPS original-data batch

N09D qualifies `cn.ens_t2m` for CMA-GEPS ORIG initialized at 2026-11-02 12 UTC,
valid at +24h, using control 0 and perturbations 1, 2 and 3. Each original has
720 × 1440 points and declares 31 ensemble forecasts. This is an explicitly
selected subset; it does not qualify the complete 31-member ensemble.

The public parameter is `cedarkit.t2m`, at 2 m, in K. Member plans select an
explicit control or perturbation role and convert the absolute temperatures to
°C. Member aliases such as `m1` and `m001` cannot count the same native member
twice. Public field identities, clocks, finite values, grids and units are
checked before aggregation; controls and perturbations remain distinct.

MAX is a pointwise maximum, with no probability division. By default its inputs
are the three selected perturbations. `include_control_in_max: true` explicitly
adds the control, giving four inputs in this batch. `max_valid_count` records
non-missing inputs at every grid point: NaNs are excluded, and an all-missing
point remains NaN with count zero. Under `missing_policy: skip`, an absent field
reduces the realized input count; `error` rejects it. An all-missing member set,
a required control that is absent, or ambiguous matches always fails.

`PreparedEnsemble.summary()` records requested and realized IDs, missing IDs,
control inclusion, selected MAX input count and per-grid valid-count range.
The MAX retains all input identities, references and reports as provenance;
it does not inherit one member's identity or completeness report. Original
reports remain unchecked where the independent expected set is unknown.

The chart labels show model, initialization, valid time, °C and the selected
MAX population. Maps retain their projection aspect. The actual application
manifest preserves the ensemble summary, including partial input counts.

```yaml
api_version: cemc.plots/v2
kind: PlotTask
source:
  dataset: cma_geps
  overrides:
    storage_base: /CMADAAS
time:
  start_time: '2026110212'
  forecast_start: 24h
  forecast_time: 24h
  forecast_interval: 24h
runtime:
  output_dir: /tmp/geps-ensemble-temperature
  missing: fail
  workers: 1
  shared_reads: true
plots:
  cn.ens_t2m:
    member_ids: [m001, m002, m003]
    control_id: ctl
    include_control_in_max: false
    missing_policy: error
    model: CMA-GEPS
    columns: 3
```

The source qualification and controlled missing-point checks belong to N09D.
N10E separately accepts the exact installed package/resource cohort, incompatible
mixtures and complete-cohort recovery. Other cycles, members, model populations,
probabilities and live service availability remain outside this batch.
