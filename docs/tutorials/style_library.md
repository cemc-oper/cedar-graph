---
mystnb:
  execution_mode: 'off'
---

# 业务样式库

cedar-graph 把 CEMC 业务色标集中在 `cedar_graph/styles/cn/` 下的
YAML 样式文件中，每个文件对应一个要素（或要素+层次）。样式文件的
schema、levels/colormap/highlight/units 等字段写法见 cedarkit-plots
的样式库编写指南；本文只介绍 cedar-graph 这一层的组织方式。

## 加载机制

`cedar_graph/styles/__init__.py` 定义 `STYLE_PATHS` 指向
`styles/cn/`，并经理事 entry point `cedarkit.plots.styles` 注入
cedarkit-plots 的默认样式注册表——安装 cedar-graph 后，
{func}`~cedarkit.plots.style.registry.get_default_registry`
自动包含全部业务样式，优先级高于 cedarkit-plots 内置样式
（同 id 后加载者胜，匹配时业务样式优先）。

同一文件还注册了几个共享 RGB 表（`register_rgb_table`），供多个
样式文件经 `colormap: { rgb_table: <name> }` 引用：

| RGB 表 | 用途 |
|---|---|
| `cn_hgt20` | 500 hPa 高度 / 海平面气压（`h_500`、`psl`） |
| `cn_ws15` | 10 m / 850 hPa 风速（`ws_10m`、`ws_850`） |
| `cn_cr19` | 雷达组合反射率（`cdbz`） |
| `cn_pte` | 假相当位温（NCL 子集 + 追加白色） |
| `cn_tdew` | 温度露点差（NCL testcmap + 两色） |
| `cn_shr` | 垂直风切变（NCL 表 + 用户色拼接） |

复合色表（NCL 子集拼接附加颜色）在 Python 侧用 cedarkit-plots 的
colormap 辅助函数构建后注册，YAML 保持纯声明式。

## 样式清单

| 文件 | 要素 | 变体 |
|---|---|---|
| `t2m.yml` | 2 米温度 | `cn_summer` / `cn_winter`（配方按月份 select） |
| `rh2m.yml` | 2 米相对湿度 | — |
| `h_500.yml` | 500 hPa 高度 | `cn_dagpm` / `cn_ws`，588 highlight |
| `psl.yml` | 海平面气压 | — |
| `kidx.yml` | K 指数 | `cn_fill` / `cn_line` |
| `wind.yml` | 风羽 | `cn`（barb） |
| `ws_10m.yml` / `ws_850.yml` | 风速填色 | — |
| `rain.yml` | 降水 | `cn` / `cn_prep` / `cn_1h`…`cn_24h` 等 7 变体 |
| `sf.yml` / `rain_snow.yml` | 雪 / 雨夹雪 | — |
| `cdbz.yml` | 雷达组合反射率 | — |
| `bli.yml` / `cape.yml` / `cin.yml` | 对流参数 | — |
| `div.yml` / `qdiv.yml` | 散度 / 水汽通量散度 | — |
| `pte_diff.yml` | 假相当位温差 | — |
| `t_dew_t.yml` | 温度露点差 | 3 变体（0 度线 RGBA 透明） |
| `shr.yml` | 垂直风切变 | 色标入库，levels 由 NCL nice-values 运行时计算 |

## 新增一个业务样式

1. 在 `cedar_graph/styles/cn/` 下新建 `<id>.yml`，`id` 与文件名一致；
2. 写 `criteria`（cemc 要素名 / ecCodes 名 + 层次码），定义至少一个
   变体与 `optimal`；
3. 需要共享色表时在 `styles/__init__.py` 里 `register_rgb_table`；
4. 用 `get_default_registry().get_style("<id>")` 验证构建结果，
   或在配方图层里以 `"<id>:<variant>"` 引用。

样式 id 命名约定：cemc 要素名（`t2m`、`psl`）；要素+层次样式用
"cemc 名 + 层次值"（`h_500`、`ws_850`）。

```{tip}
修改样式文件后如果注册表里看不到新样式，检查 cedar-graph 是否为
可编辑安装且 entry point 元数据未过期（重装一次
`pip install -e .` 即可）。
```
