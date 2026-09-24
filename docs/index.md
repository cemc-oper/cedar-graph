---
mystnb:
  execution_mode: 'off'
---

# cedar-graph

`cedar-graph` 面向 CEMC 预报产品，提供 workflow 产品、数据 provider 和便捷绘图
入口。内置产品使用 `cedarkit.plots/v3` recipe，经静态编译和数据执行后通过
`cedarkit-plots` 的 `Panel`/`Chart` 内容模型渲染。

文档样例固定使用 `cedar_graph.testing.MockDataSource` 合成数据，不需要业务数据
文件。产品 ID、参数和输出图见 {doc}`gallery/index`。

## 推荐阅读

- {doc}`getting_started/install`：安装和真实数据依赖。
- {doc}`tutorials/quick_plot`：从 CMADaaS 挂载目录快速出图。
- {doc}`tutorials/manual_plot`：选择 workflow 产品并传入 provider。
- {doc}`tutorials/mock_data`：用确定性合成数据运行相同产品。
- {doc}`tutorials/recipe` 与 {doc}`tutorials/workflow_plugins`：v3 recipe、CLI 和算子/资源插件。
- {doc}`tutorials/style_library`：调用 plots 内置的 CEMC 与通用样式。
- {doc}`api/index`：provider、产品和公开辅助接口。
- {doc}`changelog`：当前开发版迁移说明。

```{toctree}
:hidden:
:caption: 入门

getting_started/install
tutorials/quick_plot
```

```{toctree}
:hidden:
:caption: 使用

getting_started/concepts
tutorials/manual_plot
tutorials/mock_data
tutorials/recipe
tutorials/workflow_plugins
tutorials/style_library
```

```{toctree}
:hidden:
:caption: 产品图集

gallery/index
```

```{toctree}
:hidden:
:caption: 参考

api/index
changelog
```
