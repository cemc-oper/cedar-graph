---
mystnb:
  execution_mode: 'off'
---

# workflow recipe 与插件

cedar-graph 通过 `cedarkit.plots/v3` workflow 暴露内置产品。当前打包的 19 份
YAML recipe 由 `cedarkit.plots.recipes` entry point 提供；可复用业务计算通过
`cedarkit.plots.ops` 注册。注册函数返回资源/描述符，不在 import 时修改全局表。

内置算子声明为纯函数且可复用，并通过明确输入/输出数量表达数据依赖。需要额外
字段的算子应在 workflow 描述静态请求依赖，执行函数只负责计算，不应自己读取
provider。

## 校验和预览

从 cedar-graph 仓库根目录执行：

```bash
uv sync --extra test
uv run cedarkit-plots recipe validate src/cedar_graph/recipes/workflow --json
uv run cedarkit-plots recipe plan \
  src/cedar_graph/recipes/workflow/cn/rain_24h.yaml \
  --start-time 2024-07-01T00:00Z --forecast-time 24h --format json
```

`validate` 检查 schema 和 recipe 引用；`plan` 显示规范字段 ID、运算节点与读取
分组。这些命令都不创建 provider、不读取 GRIB 字段或渲染。插件发现按稳定顺序
执行，重复算子 ID 会报告冲突来源。

## 新增 recipe 与算子

新 recipe 应使用稳定 parameter ID 和明确的 `data.units`、温度语义；Style 的
expected units 只校验已准备数据。产品季节或时段选择由产品参数明确表达。只有
多个产品会共享且具有清晰输入/输出契约的数据计算，才应注册为 `OpDescriptor`。

改动后运行 recipe 目录校验、plan JSON 预览、对应合成数据数值测试与渲染测试。数值
比较应核对 dims、coords、attrs、units、NaN mask 和数组值；PNG 不能替代数据对拍。
Recipe 字段及 CLI 选项见底层库的
[v3 recipe 文档](https://github.com/cemc-oper/cedarkit-plots/blob/main/docs/tutorials/recipe_v3.md)。

## 公共查询接入示例：现有 `cn.t2m` 产品

假设 `snapshot` 是调用方固定版本的 reki `CatalogSnapshot`，目录中的 `grid`
绑定一个受控 GRIB file-pattern，`path` 是该模式内的单个 2 米温度 GRIB2 文件：

```python
from cedar_graph.data import RekiProvider
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedarkit.plots.workflow.plan import CompileContext

product = select_workflow_product("cn.t2m")
context = CompileContext(start_time="2026-08-30T00:00:00Z", forecast_time="24h",
                         params={"style_variant": "cn_summer"})
plan = product.compile(context)
with RekiProvider.from_query_catalog(
    snapshot, "grid", native_parameters={"cedarkit.t2m": "2t"},
    candidate_paths=[path], index_policy="off",
) as provider:
    availability = plan.check_available(provider)
    assert availability.executable
    result = plan.execute(provider, registry=product.discovery.ops)
    temperature_c = result.outputs["temperature"]
```

编译计划保留产品节点身份；公共 Query 只描述数据字段。provider 读取的原生字段
单位为 K，工作流已有单位节点将最终产品数据转换为 `degC`。生成临时合成 GRIB2、
对比直接 reki/CLI/provider 引用、数组与单位，并检查冷/热解码计数的完整示例可从
项目根目录运行 `uv run --offline pytest tests/mock/test_public_query_provider.py -q`。
样本不写入 Git，也不声称与业务产品数值相同。未给出的参数映射、成员角色或
公共协议尚不支持的条件会明确失败。
