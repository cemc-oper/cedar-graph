# Configuration file for the Sphinx documentation builder.
#
# Full reference:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from __future__ import annotations

from datetime import datetime
from importlib import metadata as importlib_metadata


# -- Project information ---------------------------------------------------

project = "cedar-graph"
author = "developers at cemc-oper"
copyright = f"{datetime.now():%Y}, {author}"

try:
    release = importlib_metadata.version("cedar-graph")
except importlib_metadata.PackageNotFoundError:
    release = "0.0.0"
version = ".".join(release.split(".")[:2])


# -- General configuration -------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_nb",
    "sphinx_copybutton",
    "sphinx_design",
]

# MyST / MyST-NB
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

# Default behaviour for executable markdown / notebooks. Pages opt out via
# the ``mystnb`` front matter when they should not execute on each build.
nb_execution_mode = "auto"
nb_execution_timeout = 180
nb_execution_allow_errors = False
nb_merge_streams = True

# Hide noisy loguru DEBUG stderr that plot modules emit.
nb_remove_code_outputs = False
nb_output_stderr = "remove"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# Each plot module redefines its own ``PlotMetadata`` / ``PlotData``
# dataclasses. Because they all inherit ``BasePlotMetadata`` and share
# the ``start_time`` / ``forecast_time`` / ``system_name`` fields,
# autodoc reports a "duplicate object description" warning for every
# such field. The duplicates are documentation-correct, so we leave the
# warnings on but do not promote them to errors (Read the Docs
# `.readthedocs.yaml` already sets ``fail_on_warning: false``).

source_suffix = {
    ".md": "myst-nb",
    ".ipynb": "myst-nb",
    ".rst": "restructuredtext",
}

# Auto-detect ``.md`` files as notebooks when they declare a ``kernelspec``
# front-matter. Files without one are treated as plain MyST markdown.
nb_render_markdown_format = "myst"

language = "zh_CN"


# -- Options for autodoc / autosummary -------------------------------------

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "description"
autosummary_generate = True
napoleon_numpy_docstring = True
napoleon_google_docstring = False


# -- Intersphinx -----------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "xarray": ("https://docs.xarray.dev/en/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}


# -- HTML output (sphinx-book-theme) ---------------------------------------

html_theme = "sphinx_book_theme"
html_title = "cedar-graph"
html_static_path = ["_static"]

html_theme_options = {
    "repository_url": "https://github.com/cemc-oper/cedar-graph",
    "repository_branch": "main",
    "path_to_docs": "docs",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "use_download_button": True,
    "home_page_in_toc": True,
    "show_navbar_depth": 2,
    "show_toc_level": 2,
    "navigation_with_keys": False,
}

# Headers / favicon are optional; placeholders kept commented out.
# html_logo = "_static/logo.png"
# html_favicon = "_static/favicon.ico"


# -- Matplotlib + caching --------------------------------------------------
# We don't force a non-interactive backend here, because MyST-NB launches
# Jupyter kernels for executable pages and they should default to the
# inline backend so figures render. The kernel runs in a subprocess,
# so the only thing we need is for matplotlib not to require a display
# server, which the inline backend already arranges.