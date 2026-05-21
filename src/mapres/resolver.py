import re
from .datamap import DataMap, syntax
from .cache import LRUCache
from .layers import Layer, LayerStack
from .exceptions import MapResError, MissingKeyError, MapSyntaxError


class MapResolver:
    """
    Core resolution engine for mapres.

    Handles:
    - pipeline stages
    - syntax providers
    - layered maps
    - context substitution
    - recursive multi-pass resolution
    - optional caching
    """
    def __init__(
        self,
        layers: list | None = None,
        syntax: list | None = None,
        pipeline: list | None = None,
        cache: bool = False,
        cache_size: int = 1024,
        max_depth: int = 5
    ):
        self.layers = layers or LayerStack()
        self.syntax = syntax or []
        self.pipeline = pipeline or []
        self.cache_enabled = cache
        self.cache = LRUCache(cache_size) if cache else None
        self.max_depth = max_depth

    # pipeline
    def _apply_pipeline(self, text: str, ctx: dict) -> str:
        try:
            for stage in self.pipeline:
                text = stage(text, ctx, self)
            return text
        except Exception as exc:
            raise MapResError(f"Pipeline stage failed: {exc}") from exc

    # syntax providers
    def _apply_syntax(self, text: str, ctx: dict) -> str:
        for provider in self.syntax:
            pattern = provider.pattern
            d = provider.get_map(ctx, self)
            def repl(match: re.Match) -> str:
                k = match.group(1)
                if k not in d:
                    raise MissingKeyError(f"Missing key '{k}' in syntax provider {provider}")
                return str(d[k])
            try:
                text = re.sub(pattern, repl, text)
            except re.error as exc:
                raise MapSyntaxError(
                    f"Regex error in syntax provider {provider}: {exc}"
                ) from exc
        return text

    # layered maps
    def _apply_maps(self, text: str, ctx: dict, layerstack: LayerStack):
        syntax_patterns = []
        for m in layerstack:
            if isinstance(m, type) and hasattr(m, "as_map"):
                m = m()
            if hasattr(m, "as_map"):
                syntax_patterns.append(m.get_syntax())
            elif isinstance(m, dict):
                pattern = ctx.get("syntax")
                if pattern:
                    syntax_patterns.append(pattern)
        syntax_patterns = list(dict.fromkeys(syntax_patterns))
        for pattern in syntax_patterns:
            def repl(match: re.Match):
                k = match.group(1)
                for m in layerstack:
                    layer = m
                    if isinstance(layer, type) and hasattr(layer, "as_map"):
                        layer = layer()
                    if hasattr(layer, "as_map"):
                        d = layer.as_map()
                    elif isinstance(layer, dict):
                        d = layer
                    else:
                        continue
                    if k in d:
                        return str(d[k])

                if k in ctx:
                    return str(ctx[k])

                raise MissingKeyError(f"Missing key '{k}' in any layer or context")

            try:
                text = re.sub(pattern, repl, text)
            except re.error as exc:
                raise MapSyntaxError(f"Regex error in syntax pattern {pattern}: {exc}") from exc
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
                raise MissingKeyError(f"Missing ctx key '{k}'")
            return str(d[k])
        try:
            return re.sub(pattern, repl, text)
        except re.error as exc:
            raise MapSyntaxError(f"Regex error in ctx syntax: {exc}") from exc

    # one pass
    def _resolve_once(self, text: str, ctx: dict, layerstack: LayerStack) -> str:
        text = self._apply_pipeline(text, ctx)
        text = self._apply_syntax(text, ctx)
        text = self._apply_maps(text, ctx, layerstack)
        text = self._apply_ctx(text, ctx)
        return text

    # recursion
    def _recursive(self, text: str, ctx: dict, layerstack: LayerStack) -> str:
        current = text
        for _ in range(self.max_depth):
            result = self._resolve_once(current, ctx, layerstack)
            if result == current:
                return result
            current = result
        return current

    # public api
    def res(
        self,
        text: str,
        *,
        extra_maps: dict | None = None,
        override_maps: dict | None = None,
        **ctx
    ) -> str:
        """
        Resolve a string using maps, syntax providers, pipeline, and context.
        """
        try:
            if override_maps is not None:
                temp = LayerStack([Layer("override", override_maps, priority=0)])
                return self._recursive(text, ctx, temp)

            if extra_maps:
                temp = self.layers.clone()
                temp.add_layer(Layer("extra", extra_maps, priority=999))
                return self._recursive(text, ctx, temp)

            if self.cache_enabled:
                key = (text, tuple(sorted(ctx.items())))
                cached = self.cache.get(key)
                if cached is not None:
                    return cached

            result = self._recursive(text, ctx, self.layers)

            if self.cache_enabled:
                self.cache.set(key, result)

            return result

        except MapResError:
            raise
        except Exception as exc:
            raise MapResError(f"Unhandled resolver error: {exc}") from exc


# global resolver
_DEFAULT = MapResolver()

def res(text: str, **ctx) -> str:
    """
    Resolve using the global default resolver.
    """
    return _DEFAULT.res(text, **ctx)
