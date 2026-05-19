from importlib.metadata import version as _pkg_version, PackageNotFoundError
from types import SimpleNamespace

# Package version
try:
    __version__ = _pkg_version('mapres')
except PackageNotFoundError:
    __version__ = '0.0.0'

from .resolver import MapResolver, res
from .datamap import DataMap, datamap, syntax
from .layers import Layer, LayerStack

# maps
from .maps.color import ColorMap, ascii_colors, mc_colors, strip_colors
from .maps.time import TimeMap, time_tk

# namespaces
maps = SimpleNamespace(
    ColorMap = ColorMap,
    ascii_colors = ascii_colors,
    mc_colors = mc_colors,
    strip_colors = strip_colors,
    TimeMap = TimeMap,
    time_tk = time_tk,
)

__all__ = [
    'MapResolver',
    'res',
    'DataMap',
    'datamap',
    'syntax',
    'Layer',
    'LayerStack',

    # maps
    'ColorMap',
    'ascii_colors',
    'mc_colors',
    'strip_colors',
    'TimeMap',
    'time_tk',

    # namespaces
    'maps',
]