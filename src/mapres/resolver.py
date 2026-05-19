import re
from .datamap import DataMap, syntax
from .cache import LRUCache
from .layers import Layer, LayerStack

class MapResolver:
    def __init__(self, layers=None, syntax=None, pipeline=None, cache=False, cache_size=1024, max_depth=5):
        self.layers = layers or LayerStack()
        self.syntax = syntax or []
        self.pipeline = pipeline or []
        self.cache_enabled = cache
        self.cache = LRUCache(cache_size) if cache else None
        self.max_depth = max_depth

    # pipeline
    def _apply_pipeline(self, text, ctx):
        for stage in self.pipeline:
            text = stage(text, ctx, self)
        return text

    # syntax providers
    def _apply_syntax(self, text, ctx):
        for provider in self.syntax:
            pattern = provider.pattern
            d = provider.get_map(ctx, self)
            def repl(match):
                k = match.group(1)
                return str(d.get(k, match.group(0)))
            text = re.sub(pattern, repl, text)
        return text

    # layered maps
    def _apply_maps(self, text, ctx, layerstack):
        for m in layerstack:
            if isinstance(m, type) and hasattr(m, "as_map"):
                m = m()
            if hasattr(m, "as_map"):
                pattern = m.get_syntax()
                d = m.as_map()
            elif isinstance(m, dict):
                pattern = ctx.get("syntax")
                if not pattern:
                    continue
                d = m
            else:
                continue
            def repl(match):
                k = match.group(1)
                return str(d.get(k, match.group(0)))
            text = re.sub(pattern, repl, text)
        return text

    # ctx
    def _apply_ctx(self, text, ctx):
        if not ctx:
            return text
        pattern = syntax.braces
        d = ctx
        def repl(match):
            k = match.group(1)
            return str(d.get(k, match.group(0)))
        return re.sub(pattern, repl, text)

    # one pass
    def _resolve_once(self, text, ctx, layerstack):
        text = self._apply_pipeline(text, ctx)
        text = self._apply_syntax(text, ctx)
        text = self._apply_maps(text, ctx, layerstack)
        text = self._apply_ctx(text, ctx)
        return text

    # recursion
    def _recursive(self, text, ctx, layerstack):
        current = text
        for _ in range(self.max_depth):
            result = self._resolve_once(current, ctx, layerstack)
            if result == current:
                return result
            current = result
        return current

    # public api
    def res(self, text, *, extra_maps=None, override_maps=None, **ctx):
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

# global resolver
_DEFAULT = MapResolver()

def res(text, **ctx):
    return _DEFAULT.res(text, **ctx)
