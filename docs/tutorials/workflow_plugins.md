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

可先从 cedar-graph 项目根目录运行完整离线示例；脚本创建临时合成 GRIB2，在退出时清理文件：

```bash
uv run --offline python docs/examples/public_query_t2m.py
```

示例源码在 [public_query_t2m.py](../examples/public_query_t2m.py)。已有文件可直接用
`file` source 声明路径；文件位置无需登记到目录。`dataset` 在这里选择 CMA-GFS 的
业务参数和原生字段映射，提供其他映射时可以显式传入 `context`。reki 本身也支持
不带 dataset、通过 `native` 条件查询任意 GRIB 文件。

```python
from cedar_graph.data import RekiProvider
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedarkit.plots.workflow.plan import CompileContext

product = select_workflow_product("cn.t2m")
context = CompileContext(start_time="2026-08-30T00:00:00Z", forecast_time="24h",
                         params={"style_variant": "cn_summer", "model": "CMA-GFS"})
plan = product.compile(context)
source = {"kind": "file", "path": str(path), "dataset": "cma_gfs_gmf"}
with RekiProvider(source) as provider:
    availability = plan.check_available(provider)
    assert availability.executable
    result = plan.execute(provider, registry=product.discovery.ops)
    temperature_c = result.outputs["temperature"]
    reports = provider.query_reports
    trace = provider.trace
```

provider 使用当前公共接口 `from_source(source, context=...) → sel(queries) → one() →
to_xarray()`。reki 返回 Dataset；绘图适配层只移除已知且长度为一的 time、step、member
和垂直维度，保留对应标量坐标以及完整空间维度。多个变量或非单值业务维度会显式报错。
字段身份、原生单位和起报/有效时间随 DataArray 传递，已有单位节点将 K 转为 `degC`。
图面显示模式、起报时间、有效时间和预报时效；`params.model` 控制模式文字。

`provider.trace` 每条记录包含节点、状态、结构化错误码、`query_report`、实际
`field_identity` 和 `source_reference`，可以用 `dataclasses.asdict()` 写入运行清单。
DataArray 的 `cedarkit_query_report`、`field_identity` 和 `source_reference` 属性为 JSON
字符串。关闭 provider 会释放自身 QuerySource 和缓存，保留报告快照；外部注入的
CMADaaS client 由调用方关闭。直接 service source 的预检查只做 explain，结果为
`unknown`；文件预检查扫描字段头而不解码数值。没有对 region 做隐式裁剪。

从项目根目录运行 `uv run --offline pytest tests/mock/test_public_query_provider.py -q`
可核对直接 reki Dataset 与 provider 的字段引用、全数组、单位、时间、零预检查解码和
缓存隔离。样本不写入 Git，也不声称与业务产品数值相同。历史 T15 的 CLI 一致性
验收义务仍保留；当前 reki CLI 尚未接入本公共 Request 入口，因此这部分须在 CLI
迁移时重开，不能由绘图测试替代。

旧 `SourceSpec`、`from_query_catalog` 和其 CatalogSnapshot/CollectionSession
API 已移除，调用方须使用上述 source mapping 与公共 Request。
旧 CMADaaS 高层绑定 API 也已移除，该路径会给出 `unsupported`，请使用当前公共
CMADaaS source 声明。未支持的条件会明确失败，不回退到默认字段。
