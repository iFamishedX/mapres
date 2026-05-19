from importlib.metadata import version as _pkg_version, PackageNotFoundError

# Package version
try:
    __version__ = _pkg_version('mapres')
except PackageNotFoundError:
    __version__ = '0.0.0'

from .resolver import MapResolver, res
from .datamap import DataMap, datamap
from .syntax import Syntax

__all__ = [
    'MapResolver',
    'res',
    'DataMap',
    'datamap',
    'Syntax'
]
