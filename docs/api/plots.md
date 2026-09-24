---
mystnb:
  execution_mode: 'off'
---

# workflow 绘图产品

内置产品将版本化 workflow recipe 编译为字段请求，经 provider 执行，再渲染
调用方所有的 Panel。诊断运算注册为 workflow ops，不再提供并行的
`load_data`/`plot` 产品 API。

产品选择、静态编译、集合请求和公开类型的完整签名见
[workflow 产品 API](recipes.md)。数据 provider 和业务算子接口见[数据 API](data.md)。
