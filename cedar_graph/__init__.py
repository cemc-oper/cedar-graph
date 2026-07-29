from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("cedar_graph")
except PackageNotFoundError:
    # package is not installed
    pass
