# cedar-graph

![Maturity-Sandbox](https://img.shields.io/badge/Maturity-Sandbox-F9D71C)
![GitHub Release](https://img.shields.io/github/v/release/cemc-oper/cedar-graph)
![PyPI - Version](https://img.shields.io/pypi/v/cedar-graph)
![GitHub License](https://img.shields.io/github/license/cemc-oper/cedar-graph)
![GitHub Action Workflow Status](https://github.com/cemc-oper/cedar-graph/actions/workflows/ci.yaml/badge.svg)

`cedar-graph` is a high-level plotting library for CEMC numerical weather
prediction products, including CMA-GFS, CMA-MESO, CMA-TYM, and CMA-GEPS. Built
on [reki](https://github.com/cemc-oper/reki), `cedarkit-comp`, and
[cedarkit-plots](https://github.com/cemc-oper/cedarkit-plots), it packages data
lookup, field loading, processing, and plotting into reusable product
definitions.

> This project is at the Sandbox maturity level. Its public API, recipes, and
> supported products may still evolve.

## Features

- Define most products declaratively with YAML recipes, covering data fields,
  transformations, layers, styles, titles, and colorbars.
- Support complex diagnostic products through Python plot modules with the same
  public interface as recipe-backed products.
- Run products from a compact `quick_plot` interface against a CMADaaS-mounted
  data directory, or invoke the loading and plotting stages directly in
  applications and notebooks.
- Keep operational styles in a reusable CEMC style library.
- Switch between GRIB2 data in a CMADaaS-mounted directory and deterministic
  synthetic data for tests and documentation.

## Installation

Install from PyPI:

```bash
pip install cedar-graph
```

For development in this workspace, install dependencies and run the mock test
suite:

```bash
cd repo/cedar-graph
uv sync --extra test
pytest
```

`cedar-graph` uses `reki` and ecCodes to read GRIB2 data from a CMADaaS-mounted
directory. The mock examples and tests do not require either. See the
[installation guide](docs/getting_started/install.md) for details.

## Quick plot from a CMADaaS-mounted directory

`quick_plot` is the shortest path from a product name to a figure. It uses
`LocalDataSource` and reki's `cmadaas` local-path configuration. Set
`storage_base` to the mount point; the default below is `/CMADAAS`.

```python
from cedar_graph.quickplot import quick_plot

quick_plot(
    plot_type="cn.t2m",
    system_name="CMA-GFS",
    start_time="2024073000",
    forecast_time="48h",
    data_class="cmadaas",
    storage_base="/CMADAAS",
)
```

For a custom region, pass product-specific settings such as `area_name` and
`area_range`:

```python
from cedar_graph.quickplot import quick_plot
from cedarkit.plots.types import AreaRange

quick_plot(
    plot_type="cn.wind_10m",
    system_name="CMA-MESO",
    start_time="2024073000",
    forecast_time="48h",
    data_class="cmadaas",
    storage_base="/CMADAAS",
    area_name="NorthEast",
    area_range=AreaRange.from_tuple((108, 137, 37, 55)),
)
```

The mounted-directory workflow is local file access; it does not use the
CMADaaS remote service or require CMADaaS credentials. The directory layout
must match the reki templates for the selected system.

For portable scripts, notebooks, and debugging, use a product definition with
an explicit data source instead. The [manual plotting tutorial](docs/tutorials/manual_plot.md)
shows the same workflow using `MockDataSource`, which works without access to
operational data. To read mounted data in that workflow, create
`LocalDataSource(system_name="CMA-GFS", data_class="cmadaas",
storage_base="/CMADAAS")`.

## Product model

Each product is provided by either a YAML recipe under `cedar_graph/recipes/`
or a Python module under `cedar_graph/plots/`. Both expose the same three-part
interface:

```python
PlotMetadata                 # Product metadata and product-specific options
load_data(data_loader, ...)  # Source data to fields ready for plotting
plot(plot_data, metadata)    # Fields to a cedarkit.plots Panel
```

The loader searches YAML recipes first, then Python modules. This makes product
type names such as `cn.t2m`, `cn.h_500_psl`, and `cn.shr.default` consistent
across quick plots, applications, tests, and documentation.

Available products include surface fields, upper-air analyses, precipitation,
convection diagnostics, wind shear, and moisture diagnostics. Browse the
[gallery](docs/gallery/index.md) for the complete, rendered catalogue.

## Documentation

- [Installation](docs/getting_started/install.md): runtime dependencies and
  source-based development.
- [Core concepts](docs/getting_started/concepts.md): data sources, loaders,
  product definitions, and `quick_plot`.
- [Quick plotting](docs/tutorials/quick_plot.md): CMADaaS-mounted-directory
  usage and product-specific arguments.
- [Manual plotting](docs/tutorials/manual_plot.md): explicitly load data and
  render a product, including a portable mock-data example.
- [Mock data](docs/tutorials/mock_data.md): deterministic synthetic data used
  by tests and documentation.
- [Recipes and plugins](docs/tutorials/recipe.md): write and extend YAML
  product definitions.
- [Style library](docs/tutorials/style_library.md): manage CEMC plotting
  styles.
- [Gallery](docs/gallery/index.md): rendered examples of all supported
  products.
- [API reference](docs/api/index.md): generated Python API documentation.
- [Changelog](docs/changelog.md): release history.

## Documentation structure

Keep this README as the project entry point. Detailed user and maintainer
documentation belongs under `docs/`:

```text
README.md                         Project overview, installation, mounted-directory quick plot, documentation links
docs/
├── getting_started/              Installation and shared concepts
├── tutorials/                    Quick plotting, manual workflow, mock data, recipes, and styles
├── gallery/                      Runnable product examples, organized by final figure
├── api/                          Code-synchronized module and object reference
└── changelog.md                  Release history
```

When adding a product, include a recipe or plot module, tests using mock data,
and a gallery entry. Add API documentation for stable public interfaces rather
than duplicating tutorial content.

## License

Copyright &copy; 2024-2026, developers at cemc-oper.

`cedar-graph` is licensed under the [Apache License 2.0](LICENSE).
