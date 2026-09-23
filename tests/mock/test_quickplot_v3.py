import pandas as pd
import pytest
import reki

from cedar_graph.metadata import ProductMetadata
from cedar_graph.quickplot import show_plot
from cedar_graph.recipes.workflow_product import WorkflowProduct
from cedar_graph.testing import MockDataSource


def test_product_metadata_normalizes_times_without_mutating_settings():
    settings = {"system_name": "CMA-GFS", "start_time": "2026-07-16", "forecast_time": "24h",
                "first_level": 3000}
    metadata = ProductMetadata.from_settings(settings)
    assert metadata.start_time == pd.Timestamp("2026-07-16")
    assert metadata.forecast_time == pd.Timedelta("24h")
    assert metadata.compile_context().params == {"first_level": 3000}
    assert "first_level" in settings


def test_show_plot_uses_v3_product_and_closes_only_owned_panel(monkeypatch):
    provider = MockDataSource(resolution=10)
    events = []

    class Panel:
        def show(self):
            events.append("show")

        def close(self):
            events.append("close")

    def fake_run(self, actual_provider, context):
        assert actual_provider is provider
        assert context.params["style_variant"] == "cn_summer"
        return Panel()

    monkeypatch.setattr(WorkflowProduct, "run", fake_run)
    show_plot("cn.t2m", {"system_name": "CMA-GFS", "start_time": "2026-07-16",
                         "forecast_time": "24h"}, {"provider": provider})
    assert events == ["show", "close"]
    assert provider.fetch_many is not None


def test_show_plot_closes_panel_when_show_fails(monkeypatch):
    events = []

    class Panel:
        def show(self):
            raise RuntimeError("display failed")

        def close(self):
            events.append("close")

    monkeypatch.setattr(WorkflowProduct, "run", lambda *args: Panel())
    with pytest.raises(RuntimeError, match="display failed"):
        show_plot("cn.t2m", {"system_name": "CMA-GFS", "start_time": "2026-07-16",
                             "forecast_time": "24h"}, {"provider": MockDataSource(resolution=10)})
    assert events == ["close"]


def test_show_plot_closes_its_provider_after_plot_failure(monkeypatch):
    events = []

    class Provider:
        def __init__(self, source_spec):
            assert isinstance(source_spec, reki.SourceSpec)

        def close(self):
            events.append("provider closed")

    monkeypatch.setattr("cedar_graph.quickplot.RekiProvider", Provider)
    monkeypatch.setattr(WorkflowProduct, "run",
                        lambda *args: (_ for _ in ()).throw(RuntimeError("render failed")))
    with pytest.raises(RuntimeError, match="render failed"):
        show_plot("cn.t2m", {"system_name": "CMA-GFS", "start_time": "2026-07-16",
                             "forecast_time": "24h"}, {"source_spec": reki.SourceSpec("local")})
    assert events == ["provider closed"]
