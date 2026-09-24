# 产品图集

图集展示 workflow 产品的数据读取请求、诊断层和样式组合。`cn.t2m` 与
`cn.ens_t2m` 页面使用固定 `MockDataSource`，构建文档时由 MyST-NB 单元格动态执行，
图像作为 Sphinx 构建产物由页面引用；源文档不引用仓库内的静态图片。其他产品页给出可复用
的 workflow 配置示例；所有 mock 数据只用于检查流程与绘图接口，不代表真实预报结果。

所有 recipe 与迁移后的诊断产品通过统一 workflow 运行。集合温度产品另外显式声明
成员 ID、control、MAX 输入和缺测策略。

```{toctree}
:maxdepth: 1

t_2m
rh_2m
height_500_mslp
height_500_wind_850
wind_10m
radar_reflectivity
div_wind
k_wind
cape_wind
cin_wind
bli_wind
pte_wind
qv_div
shr
t_dew_t
rain_24h
rain_wind_10m
prep_24h
ens_t2m
```
