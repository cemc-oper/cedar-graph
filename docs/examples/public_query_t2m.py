"""Run the packaged cn.t2m workflow against one temporary GRIB2 field."""

from pathlib import Path
from tempfile import TemporaryDirectory

import eccodes

from cedar_graph.data import RekiProvider
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedarkit.plots.workflow.plan import CompileContext
from reki.catalog import load_catalog
from reki.catalog.query_binding import CatalogSnapshot


def write_sample(path: Path) -> None:
    message = eccodes.codes_grib_new_from_samples("regular_ll_pl_grib2")
    try:
        for key, value in (
            ("shortName", "2t"), ("dataDate", 20260830), ("dataTime", 0),
            ("forecastTime", 24), ("typeOfLevel", "heightAboveGround"), ("level", 2),
            ("Ni", 4), ("Nj", 3), ("latitudeOfFirstGridPointInDegrees", 50),
            ("latitudeOfLastGridPointInDegrees", 48), ("longitudeOfFirstGridPointInDegrees", 100),
            ("longitudeOfLastGridPointInDegrees", 103), ("iDirectionIncrementInDegrees", 1),
            ("jDirectionIncrementInDegrees", 1),
        ):
            eccodes.codes_set(message, key, value)
        eccodes.codes_set_values(message, [280.0 + index for index in range(12)])
        path.write_bytes(eccodes.codes_get_message(message))
    finally:
        eccodes.codes_release(message)


def main() -> None:
    with TemporaryDirectory(prefix="cedar-graph-query-") as directory:
        root = Path(directory)
        path = root / "t2m.grib2"
        write_sample(path)
        catalog = load_catalog(builtin=False, plugins=False, user=False, explicit={
            "api_version": "reki.catalog/v1", "datasets": [{"id": "grid", "source": {
                "name": "file-pattern", "args": [str(root), "t2m.grib2"]}}],
        })
        snapshot = CatalogSnapshot(catalog, "t17-local")
        product = select_workflow_product("cn.t2m")
        plan = product.compile(CompileContext(
            start_time="2026-08-30T00:00:00Z", forecast_time="24h",
            params={"style_variant": "cn_summer"},
        ))
        with RekiProvider.from_query_catalog(
            snapshot, "grid", native_parameters={"cedarkit.t2m": "2t"},
            candidate_paths=[path], index_policy="off",
        ) as provider:
            availability = plan.check_available(provider)
            assert availability.executable
            result = plan.execute(provider, registry=product.discovery.ops)
            temperature = result.outputs["temperature"]
            assert temperature.attrs["units"] == "degC"
            print(availability.requests[0].status, temperature.shape, temperature.attrs["units"])


if __name__ == "__main__":
    main()
