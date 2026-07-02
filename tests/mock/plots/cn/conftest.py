from pathlib import Path

import pytest


@pytest.fixture
def output_dir(run_base_dir, plot_name):
    d = Path(run_base_dir, "plots/cn", plot_name)
    d.mkdir(exist_ok=True, parents=True)
    return d
