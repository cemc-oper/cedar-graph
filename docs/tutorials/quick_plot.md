---
mystnb:
  execution_mode: 'off'
---

# 挂载目录快绘

`quick_plot()` 按产品 ID 选择当前 workflow 产品，从 reki catalog 解析数据集，
读取字段、执行 recipe 并显示最终 Panel。内置 YAML 产品和迁移后的诊断产品走同一
条编译/执行路径。产品清单见 {doc}`../api/recipes`。

## 从 `/CMADAAS` 读取 CMA-GFS

```python
import pandas as pd
from cedar_graph.quickplot import quick_plot

quick_plot(
    plot_type="cn.t2m",
    system_name="CMA-GFS",
    start_time=pd.Timestamp("2026-09-22 00:00:00"),
    forecast_time=pd.Timedelta("24h"),
    data_class="cmadaas",
    storage_base="/CMADAAS",
)
```

这是本地挂载文件访问，不会请求 CMADaaS 在线服务，也不需要在线服务凭据。目录
结构须匹配 reki 对所选系统的路径模板。`quick_plot()` 自己创建并在显示后关闭
Panel/provider；若需保存文件或控制窗口生命周期，请按
{doc}`manual_plot` 直接运行产品并管理返回的 Panel。

## 产品参数

recipe 声明的参数通过关键字传入。例如，K 指数图要求风场层次；降水与风场组合
图要求累计时段：

```python
quick_plot(
    plot_type="cn.kidx_wind",
    system_name="CMA-GFS",
    start_time=pd.Timestamp("2026-09-22T00:00"),
    forecast_time=pd.Timedelta("24h"),
    data_class="cmadaas",
    storage_base="/CMADAAS",
    wind_level=850,
)

quick_plot(
    plot_type="cn.rain_wind_10m",
    system_name="CMA-GFS",
    start_time=pd.Timestamp("2026-09-22T00:00"),
    forecast_time=pd.Timedelta("24h"),
    data_class="cmadaas",
    storage_base="/CMADAAS",
    interval="3h",
)
```

集合产品 `cn.ens_t2m` 使用实际扰动成员 ID，可选 control、MAX 与缺测策略。它们
不是从输入数组位置推测的，示例任务参数见 `cemc-plots-kit` 的集合 YAML。

## 没有业务挂载时

文档和测试使用 {class}`cedar_graph.testing.MockDataSource`，它实现相同 provider
协议并生成确定性合成场。无需调用 CMADaaS，也无需改 recipe；参见
{doc}`mock_data`。
