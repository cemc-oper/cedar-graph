---
mystnb:
  execution_mode: 'off'
---

# 变更记录

正式版本及发行日期以 [GitHub Releases](https://github.com/cemc-oper/cedar-graph/releases)
为准。这里记录当前开发版尚未发行的行为变化。

## 未发布

- 13 个原声明式业务产品与 5 个原 Python 诊断产品均通过统一的
  `cedarkit.plots/v3` workflow 产品接口编译、执行和渲染。
- `RekiProvider` 使用稳定 parameter ID 与 `FieldQuery` 请求本地/服务数据；
  `MockDataSource` 实现相同的字段 provider 协议，供测试和文档样例使用。
- 增加集合产品 `cn.ens_t2m`，成员身份、control、MAX 输入及缺失策略显式配置。
- CEMC 样式与 palette 由 `cedarkit-plots` 单一提供；删除 graph 自有重复样式、
  v2 recipe 和旧引擎/数据入口。
- `quick_plot()` 从 reki catalog 解析系统数据集、运行当前 workflow 并显示图形；
  直接产品调用返回的 Panel 由调用方关闭。
- 旧 recipe schema 和 `load_data`/`plot` adapter 不再支持，也不提供兼容或自动
  迁移服务。新产品使用 `cedarkit.plots/v3`。
- cn.t2m 与 cn.ens_t2m 的固定合成图由 MyST-NB 在文档构建时动态生成并内嵌到
  站点构建产物；独立 PNG 导出脚本默认写入仓库外的临时目录。
