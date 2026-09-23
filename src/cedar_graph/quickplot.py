"""Display a selected v3 Cedar Graph product from a reki provider."""

from typing import Any, Optional

import pandas as pd
import reki

from cedar_graph.data import RekiProvider

__all__ = [
    "quick_plot",
    "show_plot",
]


def quick_plot(
        plot_type: str,
        system_name: str,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        data_class: str = "od",
        storage_base: Optional[str] = None,
        data_source_kwargs: Optional[dict[str, Any]] = None,
        **plot_kwargs,
):
    """
    draw the plot and display it

    Parameters
    ----------
    plot_type
        Product ID such as ``cn.t2m`` or ``cn.shr.default``.
    system_name
        system name. default supported systems:

        * CMA-GFS：global forecast system
        * CMA-MESO：regional system (3km)
        * CMA-TYM：regional typhoon forecast system
        * CMA-MESO-1KM：regional forecast system (1km)
    start_time
        start time, such as YYYY-MM-DD HH:00:00
    forecast_time
        forecast time, such as 24h
    data_class
        data class passed to reki data finder, default is "od".
    storage_base
        storage base path passed to reki data finder.
    data_source_kwargs
        other keyword arguments passed to reki data finder.
    plot_kwargs
        other plot-specific parameters, such as ``area_range``, ``interval``.
    """
    plot_settings = dict(
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
        **plot_kwargs,
    )
    data_source_config = dict(
        data_class=data_class,
        storage_base=storage_base,
        **(data_source_kwargs or {}),
    )
    show_plot(
        plot_type=plot_type,
        plot_settings=plot_settings,
        data_source_config=data_source_config,
    )


def show_plot(plot_type: str, plot_settings: dict, data_source_config: dict):
    from cedar_graph.recipes.ensemble_product import EnsembleRequest, EnsembleT2MProduct, select_ensemble_product
    from cedar_graph.recipes.workflow_product import select_workflow_product
    from cedar_graph.metadata import ProductMetadata

    product = select_ensemble_product(plot_type) or select_workflow_product(plot_type)
    if product is None:
        raise KeyError(f"unknown v3 product {plot_type!r}")
    metadata = ProductMetadata.from_settings(plot_settings)
    source_config = dict(data_source_config)
    provider = source_config.pop("provider", None)
    owned = provider is None
    if owned:
        source_spec = source_config.pop("source_spec", None)
        if source_spec is None:
            dataset = reki.load_catalog(plugins=False, user=True).resolve(metadata.system_name)
            source_spec = reki.SourceSpec(dataset.source.name, dataset.source.args,
                {**dataset.source.kwargs, **{key: value for key, value in source_config.items()
                   if value is not None}})
        provider = RekiProvider(source_spec)
    try:
        if isinstance(product, EnsembleT2MProduct):
            prepared = product.prepare(provider, start_time=metadata.start_time,
                forecast_time=metadata.forecast_time,
                request=EnsembleRequest.from_params(metadata.params))
            panel = prepared.render()
        else:
            context = metadata.compile_context()
            if plot_type == "cn.t2m" and "style_variant" not in context.params:
                context = type(context)(start_time=context.start_time, forecast_time=context.forecast_time,
                    params={**context.params, "style_variant": "cn_summer" if 5 <= metadata.start_time.month <= 9 else "cn_winter"})
            panel = product.run(provider, context)
        try:
            panel.show()
        finally:
            panel.close()
    finally:
        if owned:
            provider.close()
