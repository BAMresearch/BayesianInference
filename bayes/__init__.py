from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("bayes")
except PackageNotFoundError:
    # package is not installed
    pass
