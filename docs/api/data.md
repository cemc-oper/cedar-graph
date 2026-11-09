---
mystnb:
  execution_mode: 'off'
---

# 数据接口

```{eval-rst}
.. automodule:: cedar_graph.data
   :members:
   :undoc-members:
   :show-inheritance:
```

## ReKi provider

`RekiProvider` 接收公开 source mapping，将 workflow 的 `BoundFieldRequest` 转为
公共 `Request` / `Query`。产品计划保留稳定 parameter ID、成员和显式时次，不保存
源路径或凭据。普通文件和本地目录使用原生 GRIB 查询；CMADaaS 使用当前公共
source 声明及已登记的具名参数。旧 `SourceSpec`、旧异常和 `from_query_catalog`
入口已移除，不能再用旧模型对象创建 provider。

```python
from cedar_graph.data import RekiProvider

with RekiProvider({"kind": "file", "path": "original.grib2", "dataset": "cma_gfs_gmf"}) as provider:
    # 将 provider 传给已编译且包含显式时次的 workflow 计划。
    pass
```

`check_many()` 对文件扫描 metadata，不解码网格值；服务预检查只做 explain，返回
`unknown`。`fetch()` / `fetch_many()` 返回带 `cedarkit_query_report`、
`field_identity` 和 `source_reference` JSON 属性的单变量 DataArray，歧义由公共
查询错误明确报告。任务内重复字段共享缓存；没有隐式 region 裁剪或层次回退。

`ProviderTrace` 记录节点、查询报告、身份、来源、耗时与结构化错误码，避免记录认证
信息。`close()` 释放 provider 自己创建的 QuerySource 和字段缓存，保留 trace / report
快照。外部注入的 CMADaaS client 仍由调用方关闭。`cache_info` 报告本 provider 的
缓存命中、未命中和当前条目数。

```{eval-rst}
.. automodule:: cedar_graph.data.provider
   :members:
```

## 数据算子

```{eval-rst}
.. automodule:: cedar_graph.data.operator
   :members:
   :undoc-members:
   :show-inheritance:
```

## 产品元信息

```{eval-rst}
.. automodule:: cedar_graph.metadata
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
```
