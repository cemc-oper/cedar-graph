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

`RekiProvider` 将 ReKi 数据源绑定到 workflow 的 `BoundFieldRequest` 协议。
产品计划保存稳定 parameter ID、FieldQuery 和时次，不保存 catalog 数据代码、源
名称或凭据。旧入口在执行边界接收 `SourceSpec`；公共查询入口
`RekiProvider.from_query_catalog(snapshot, dataset, native_parameters=...)`
接收受控目录快照与显式原生参数映射。两种入口均通过 `fetch()`/
`fetch_many()` 返回 xarray 字段，旧调用不改变。

公共入口先使用 plots 的 `public_request_from_field_request()` 和 reki 既有
`query_from_field_query()` 规范化每个字段请求，节点 ID 留在 workflow。
本地 `check_many()` 使用 metadata 定位，不解码值；`fetch_many()` 使用
reki 的 `CollectionSession.read_many()` 和文件指纹缓存，重复字段只解码一次。
返回字段的 `attrs["source_reference"]` 是该次读取的公共 `DataReference`，
可以与 CLI `reki request locate/read` 的引用对比。调用方可给有限
`candidate_paths`；省略时仅解析目录中确定性的单文件候选。原生参数与成员角色
都由调用方提供，未验证的 FieldQuery 条件会失败。`close()` 关闭 provider
持有的会话；`cache_info` 在公共入口报告原生值缓存计数。

常规本地 GRIB reader 使用 reki 的选择接口。具备 CMADaaS direct-result 能力的源会
在创建 reader 前将稳定参数 ID、具体查询与时次绑定成请求；返回的内存字段直接做
校验，不会再执行 `.sel()`。对不能只查 metadata 的服务，`check_many()` 返回
`unknown`，不会为判定可用性提前读取整个网格。
公共入口的 CMADaaS 先核对 T13 四条冻结案例和注册表 SHA256；范围外请求
报告 `invalid`，范围内远端字段仍为 `unknown`，实际读取才访问服务。

`ProviderTrace` 记录 catalog 来源、参数身份、时次和请求状态，不包含客户端配置或
认证信息。`close()` 清除 provider 自身的字段缓存与 trace；调用方负责按任务生命周
期关闭自己创建的 provider。

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
