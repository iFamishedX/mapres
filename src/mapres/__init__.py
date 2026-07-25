from importlib.metadata import version as _pkg_version, PackageNotFoundError
from types import SimpleNamespace
import sys
import importlib.abc
import importlib.util
import re

# Package version
try:
    __version__ = _pkg_version('mapres')
except PackageNotFoundError:
    __version__ = '0.0.0'

# ------------------------------------------------------------
# Public API imports
# ------------------------------------------------------------
from .resolver import MapResolver, res, setGlobalMaps, setDefaultPasses
from .datamap import DataMap, datamap, syntax
from .layers import Layer, LayerStack

# maps
from .maps.color import ColorMap, ascii_colors, mc_colors, strip_colors
from .maps.time import TimeMap, time

# namespaces
maps = SimpleNamespace(
    # color
    ColorMap=ColorMap,
    ascii_colors=ascii_colors,
    mc_colors=mc_colors,
    strip_colors=strip_colors,

    # time
    TimeMap=TimeMap,
    time=time,
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

# ------------------------------------------------------------
# Local-only literal prefix transformer
# ------------------------------------------------------------

# Matches: res"<tag>"
PREFIX_PATTERN = re.compile(r'(\bres)"([^"]*)"')

def _transform_source(code: str) -> str:
    return PREFIX_PATTERN.sub(r'\1("\2")', code)


class _MapresLoader(importlib.abc.SourceLoader):
    def __init__(self, fullname, path):
        self.fullname = fullname
        self.path = path

    def get_filename(self, fullname):
        return self.path

    def get_data(self, path):
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
        transformed = _transform_source(original)
        return transformed.encode("utf-8")


class _MapresFinder(importlib.abc.MetaPathFinder):
    def __init__(self, target_module):
        self.target_module = target_module

    def find_spec(self, fullname, path, target=None):
        # Only rewrite the module that imported mapres
        if fullname != self.target_module:
            return None

        spec = importlib.util.find_spec(fullname)
        if spec and spec.origin:
            return importlib.util.spec_from_loader(
                fullname,
                _MapresLoader(fullname, spec.origin),
                origin=spec.origin
            )
        return None


def _install_local_hook(module_name):
    sys.meta_path.insert(0, _MapresFinder(module_name))


# ------------------------------------------------------------
# Hook activation
# ------------------------------------------------------------
def __getattr__(name):
    # Detect the module that imported mapres
    frame = sys._getframe(1)
    module_name = frame.f_globals.get("__name__")

    # Install hook for that module
    _install_local_hook(module_name)

    # Expose your public API normally
    if name in __all__:
        return globals()[name]

    raise AttributeError(name)
