"""Run the packaged cn.t2m workflow against one temporary GRIB2 field."""

from pathlib import Path
from tempfile import TemporaryDirectory

import cartopy.crs  # Load PROJ before ecCodes in the combined plotting process.
import eccodes

from cedar_graph.data import RekiProvider
from cedar_graph.recipes.workflow_product import select_workflow_product
from cedarkit.plots.workflow.plan import CompileContext


def write_sample(path: Path) -> None:
    message = eccodes.codes_grib_new_from_samples("regular_ll_pl_grib2")
    try:
        for key, value in (
            ("centre", 38), ("subCentre", 0), ("tablesVersion", 4),
            ("localTablesVersion", 0), ("productionStatusOfProcessedData", 0),
            ("discipline", 0), ("parameterCategory", 0), ("parameterNumber", 0),
            ("significanceOfReferenceTime", 1), ("dataDate", 20260830), ("dataTime", 0),
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
        source = {"kind": "file", "path": str(path), "dataset": "cma_gfs_gmf"}
        product = select_workflow_product("cn.t2m")
        plan = product.compile(CompileContext(
            start_time="2026-08-30T00:00:00Z", forecast_time="24h",
            params={"style_variant": "cn_summer"},
        ))
        with RekiProvider(source) as provider:
            availability = plan.check_available(provider)
            assert availability.executable
            result = plan.execute(provider, registry=product.discovery.ops)
            temperature = result.outputs["temperature"]
            assert temperature.attrs["units"] == "degC"
            print(availability.requests[0].status, temperature.shape, temperature.attrs["units"])


if __name__ == "__main__":
    main()
