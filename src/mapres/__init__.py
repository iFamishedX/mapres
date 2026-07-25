from importlib.metadata import version as _pkg_version, PackageNotFoundError
from types import SimpleNamespace

# Package version
try:
    __version__ = _pkg_version('mapres')
except PackageNotFoundError:
    __version__ = '0.0.0'

from .resolver import MapResolver, res, setGlobalMaps, setDefaultPasses
from .datamap import DataMap, datamap, syntax
from .layers import Layer, LayerStack

# maps
from .maps.color import ColorMap, ascii_colors, mc_colors, strip_colors
from .maps.time import TimeMap, time

# namespaces
maps = SimpleNamespace(
    # color
    ColorMap = ColorMap,
    ascii_colors = ascii_colors,
    mc_colors = mc_colors,
    strip_colors = strip_colors,

    # time
    TimeMap = TimeMap,
    time = time,
)

__all__ = [
    # core modules
    'MapResolver',
    'res',
    'DataMap',
    'datamap',
    'syntax',
    'Layer',
    'LayerStack',
    'setGlobalMaps',
    'setDefaultPasses',

    # maps
    'ColorMap',
    'ascii_colors',
    'mc_colors',
    'strip_colors',
    'TimeMap',
    'time',

    # namespaces
    'maps',
]