import re
from .datamap import DataMap, syntax
from .cache import LRUCache
from .layers import Layer, LayerStack
from .exceptions import MapResError, MissingKeyError, MapSyntaxError


class MapResolver:
    '''
    Core resolution engine for mapres.

    Handles:
    - pipeline stages
    - syntax providers
    - layered maps
    - context substitution
    - multi-pass resolution (controlled by `passes`)
    - optional caching
    '''
    def __init__(
        self,
        layers: list | None = None,
        syntax: list | None = None,
        pipeline: list | None = None,
        cache: bool = False,
        cache_size: int = 1024,
        passes_default: int = 5
    ):
        self.layers = layers or LayerStack()
        self.syntax = syntax or []
        self.pipeline = pipeline or []
        self.cache_enabled = cache
        self.cache = LRUCache(cache_size) if cache else None

        # unified recursion control
        self.passes_default = passes_default

    # pipeline
    def _apply_pipeline(self, text: str, ctx: dict) -> str:
        try:
            for stage in self.pipeline:
                text = stage(text, ctx, self)
            return text
        except Exception as exc:
            raise MapResError(f'Pipeline stage failed: {exc}') from exc

    # syntax providers
    def _apply_syntax(self, text: str, ctx: dict) -> str:
        for provider in self.syntax:
            pattern = provider.pattern
            d = provider.get_map(ctx, self)

            def repl(match: re.Match) -> str:
                k = match.group(1)
                if k not in d:
                    raise MissingKeyError(f'Missing key "{k}" in syntax provider {provider}')
                return str(d[k])

            try:
                text = re.sub(pattern, repl, text)
            except re.error as exc:
                raise MapSyntaxError(
                    f'Regex error in syntax provider {provider}: {exc}'
                ) from exc

        return text

    # layered maps
    def _apply_maps(self, text: str, ctx: dict, layerstack: LayerStack):
        syntax_patterns = []

        for m in layerstack:
            if isinstance(m, type) and hasattr(m, 'as_map'):
                m = m()
            if hasattr(m, 'as_map'):
                syntax_patterns.append(m.get_syntax())
            elif isinstance(m, dict):
                pattern = ctx.get('syntax')
                if pattern:
                    syntax_patterns.append(pattern)

        syntax_patterns = list(dict.fromkeys(syntax_patterns))

        for pattern in syntax_patterns:
            def repl(match: re.Match):
                k = match.group(1)

                for m in layerstack:
                    layer = m
                    if isinstance(layer, type) and hasattr(layer, 'as_map'):
                        layer = layer()
                    if hasattr(layer, 'as_map'):
                        d = layer.as_map()
                    elif isinstance(layer, dict):
                        d = layer
                    else:
                        continue

                    if k in d:
                        return str(d[k])

                if k in ctx:
                    return str(ctx[k])

                raise MissingKeyError(f'Missing key "{k}" in any layer or context')

            try:
                text = re.sub(pattern, repl, text)
            except re.error as exc:
                raise MapSyntaxError(f'Regex error in syntax pattern {pattern}: {exc}') from exc

        return text

    # context
    def _apply_ctx(self, text: str, ctx: dict) -> str:
        if not ctx:
            return text

        pattern = syntax.braces
        d = ctx

        def repl(match: re.Match) -> str:
            k = match.group(1)
            if k not in d:
                raise MissingKeyError(f'Missing ctx key "{k}"')
            return str(d[k])

        try:
            return re.sub(pattern, repl, text)
        except re.error as exc:
            raise MapSyntaxError(f'Regex error in ctx syntax: {exc}') from exc

    # one pass
    def _resolve_once(self, text: str, ctx: dict, layerstack: LayerStack) -> str:
        text = self._apply_pipeline(text, ctx)
        text = self._apply_syntax(text, ctx)
        text = self._apply_maps(text, ctx, layerstack)
        text = self._apply_ctx(text, ctx)
        return text

    # public api
    def res(
        self,
        text: str,
        *,
        passes: int | None = None,
        extra_maps: dict | None = None,
        override_maps: dict | None = None,
        **ctx
    ) -> str:
        '''
        Resolve a string using maps, syntax providers, pipeline, and context.
        '''
        try:
            # determine number of passes
            depth = passes if passes is not None else self.passes_default

            if depth <= 0:
                raise MapResError("passes must be >= 1")

            # override maps
            if override_maps is not None:
                temp = LayerStack([Layer('override', override_maps, priority=0)])
                return self._resolve_once(text, ctx, temp)

            # extra maps
            if extra_maps:
                temp = self.layers.clone()
                temp.add_layer(Layer('extra', extra_maps, priority=999))
                return self._resolve_once(text, ctx, temp)

            # caching
            if self.cache_enabled:
                key = (text, tuple(sorted(ctx.items())))
                cached = self.cache.get(key)
                if cached is not None:
                    return cached

            # multi-pass resolution
            current = text
            for _ in range(depth):
                new = self._resolve_once(current, ctx, self.layers)
                if new == current:
                    break
                current = new

            result = current

            if self.cache_enabled:
                self.cache.set(key, result)

            return result

        except MapResError:
            raise
        except Exception as exc:
            raise MapResError(f'Unhandled resolver error: {exc}') from exc


# ----------------------------------
# ---------- SIMPLE USAGE ----------
# ----------------------------------
_DEFAULT_RESOLVER = MapResolver()        # global resolver

def setGlobalMaps(maps, *, name=None, priority=0):
    """
    Register a global map or datamap class into the default resolver.

    maps: datamap class OR dict
    name: optional layer name (default = class name or 'global')
    priority: layer priority (lower = earlier)
    """
    layer_name = name or getattr(maps, "__name__", "global")
    layer = Layer(layer_name, maps=[maps], priority=priority)
    _DEFAULT_RESOLVER.layers.add_layer(layer)

def setDefaultPasses(passes: int):
    if passes < 1:
        raise MapResError("Passes cannot be less than 1")
    _DEFAULT_RESOLVER.passes_default = passes

def res(text: str, passes=None, **ctx) -> str:
    '''
    Simple resolution using the global default resolver.
    '''
    return _DEFAULT_RESOLVER.res(text, passes=passes, **ctx)
