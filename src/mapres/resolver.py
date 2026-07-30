from .tokenizer import Tokenizer
from .parser import Parser
from .evaluator import Evaluator
from .layers import LayerStack
from .cache import LRUCache
from .exceptions import MapResError, MissingKeyError


class MapResolver:
    """
    New AST-based resolver for mapres.

    Pipeline:
        tokenize → parse → evaluate → return string

    Supports:
        - hierarchical identifiers
        - nested tokens (single argument)
        - multiple map layers
        - ctx fallback
        - caching (optional)
    """

    def __init__(self, layers=None, cache=False, cache_size=1024):
        self.layers = layers or LayerStack()
        self.cache_enabled = cache
        self.cache = LRUCache(cache_size) if cache else None

    # ---------------------------------------
    # PUBLIC API
    # ---------------------------------------
    def res(self, text: str, *, extra_maps=None, override_maps=None, **ctx) -> str:
        """
        Resolve a template string using:
            - tokenizer
            - parser
            - evaluator
            - layerstack
            - ctx
        """

        try:
            # caching
            if self.cache_enabled:
                key = (text, tuple(sorted(ctx.items())))
                cached = self.cache.get(key)
                if cached is not None:
                    return cached

            # build working layerstack
            layerstack = self._build_layerstack(extra_maps, override_maps)

            # tokenize
            tokens = Tokenizer(text).tokenize()

            # parse
            ast = Parser(tokens).parse()

            # evaluate
            result = Evaluator(layerstack, ctx).evaluate(ast)

            # store cache
            if self.cache_enabled:
                self.cache.set(key, result)

            return result

        except MissingKeyError as exc:
            mode = self._resolve_missing_key_mode()
            if mode == 'error':
                raise MapResError(f'Resolver error: {exc}') from exc
            if mode == 'silent':
                return text
            if mode == 'placeholder':
                return f'<missing:{exc.key}>'
            raise MapResError(f'Resolver error: {exc}') from exc

        except Exception as exc:
            raise MapResError(f'Resolver error: {exc}') from exc

    # ---------------------------------------
    # LAYERSTACK BUILDING
    # ---------------------------------------
    def _build_layerstack(self, extra_maps, override_maps):
        """
        Build a temporary layerstack for this resolution call.
        Supports:
            - override maps (priority 0)
            - extra maps (priority 999)
            - normal layers (existing priorities)
        """

        if override_maps is not None:
            temp = LayerStack()
            temp.add_layer(override_maps, priority=0)
            return temp

        if extra_maps is not None:
            temp = self.layers.clone()
            temp.add_layer(extra_maps, priority=999)
            return temp

        return self.layers

    def _resolve_missing_key_mode(self):
        for m in self.layers.all_maps():
            mode = getattr(m, '__missing_key__', None)
            if mode is not None:
                return mode
        return 'error'


# ---------------------------------------
# SIMPLE GLOBAL USAGE
# ---------------------------------------

_DEFAULT_RESOLVER = MapResolver()

def setGlobalMaps(maps, *, priority=0):
    """
    Register a global map or datamap instance/class/dict.
    Lower priority = earlier lookup.
    """
    if isinstance(maps, type):
        try:
            maps = maps()
        except TypeError:
            pass
    _DEFAULT_RESOLVER.layers.add_layer(maps, priority=priority)

def res(text: str, **ctx) -> str:
    """
    Simple global resolution.
    """
    return _DEFAULT_RESOLVER.res(text, **ctx)
