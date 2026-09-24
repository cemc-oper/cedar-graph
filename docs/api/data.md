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
名称或凭据。provider 在实际执行边界接收 `SourceSpec`，并通过 `fetch()`/
`fetch_many()` 返回已规范化和验证的 xarray 字段。

常规本地 GRIB reader 使用 reki 的选择接口。具备 CMADaaS direct-result 能力的源会
在创建 reader 前将稳定参数 ID、具体查询与时次绑定成请求；返回的内存字段直接做
校验，不会再执行 `.sel()`。对不能只查 metadata 的服务，`check_many()` 返回
`unknown`，不会为判定可用性提前读取整个网格。

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
