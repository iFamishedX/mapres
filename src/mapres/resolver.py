import re
from .syntax import Syntax
from .datamap import DataMap
from .cache import LRUCache

class MapResolver:
    def __init__(self, maps=None, syntax=None, pipeline=None, cache=False, cache_size=1024, max_depth=5):
        self.maps = maps or []
        self.syntax = syntax or []
        self.pipeline = pipeline or []
        self.cache_enabled = cache
        self.cache = LRUCache(cache_size) if cache else None
        self.max_depth = max_depth

    def _apply_pipeline(self, text, ctx):
        for stage in self.pipeline:
            text = stage(text, ctx, self)
        return text

    def _apply_syntax(self, text, ctx):
        for provider in self.syntax:
            pattern = provider.pattern
            d = provider.get_map(ctx, self)
            def repl(match):
                k = match.group(1)
                return str(d.get(k, match.group(0)))
            text = re.sub(pattern, repl, text)
        return text

    def _apply_maps(self, text, ctx):
        for m in self.maps:
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

    def _apply_ctx(self, text, ctx):
        if not ctx:
            return text
        pattern = Syntax.braces
        d = ctx
        def repl(match):
            k = match.group(1)
            return str(d.get(k, match.group(0)))
        return re.sub(pattern, repl, text)

    def _recursive(self, text, ctx):
        current = text
        for _ in range(self.max_depth):
            result = self._resolve_once(current, ctx)
            if result == current:
                return result
            current = result
        return current

    def _resolve_once(self, text, ctx):
        text = self._apply_pipeline(text, ctx)
        text = self._apply_syntax(text, ctx)
        text = self._apply_maps(text, ctx)
        text = self._apply_ctx(text, ctx)
        return text

    def res(self, text, **ctx):
        if self.cache_enabled:
            key = (text, tuple(sorted(ctx.items())))
            cached = self.cache.get(key)
            if cached is not None:
                return cached
        result = self._recursive(text, ctx)
        if self.cache_enabled:
            self.cache.set(key, result)
        return result

_DEFAULT = MapResolver()

def res(text, **ctx):
    return _DEFAULT.res(text, **ctx)
