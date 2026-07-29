"""
Testing utilities for ``cedar-graph``.

This subpackage provides helpers that are useful both for the test suite
and for documentation examples that need to run without access to real
NWP data on CMA-HPC. The main entry point is :class:`MockDataSource`,
a synthetic :class:`~cedar_graph.data.DataSource` that generates
deterministic 2D fields covering East Asia.
"""
from .mock_data import MockDataSource, build_mock_data_loader

__all__ = ["MockDataSource", "build_mock_data_loader"]
