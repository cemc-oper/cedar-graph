---
mystnb:
  execution_mode: 'off'
---

# 安装

## 从 PyPI 安装

```bash
pip install cedar-graph
```

会同时安装 cedar-graph 的运行时依赖：`reki`、`cedarkit-comp`、
`cedarkit-plots`、`numpy`、`pandas`、`xarray`、`matplotlib`、
`cartopy` 与 `loguru`。

## 从源码安装（uv）

cedar-graph 源码仓库位于 `cedarkit/` 工作区目录下，紧邻
`reki`、`cedarkit-comp`、`cedarkit-plots` 等姊妹包。
`pyproject.toml` 中的 `[tool.uv.sources]` 已经把这些
姊妹包配置为本地可编辑安装，因此对任一姊妹包的修改都会立即生效，
无需重新安装。

```bash
uv sync                  # 安装运行时依赖
uv sync --extra test     # 同时安装 pytest
uv sync --extra docs     # 同时安装 Sphinx + sphinx-book-theme
```

## ecCodes

通过 `reki` 读取真实 GRIB2 数据需要系统提供 **ecCodes** 库。
本文档中的所有 mock 数据示例不依赖 ecCodes，因此仅构建文档
或运行 mock 测试时无需安装 ecCodes。需要在工作站上读取真实
GRIB2 数据时，推荐通过 conda 安装：
`conda install -c conda-forge eccodes`。在 CMA-HPC 上，
ecCodes 已由系统统一提供。
