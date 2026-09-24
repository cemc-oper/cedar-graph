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
