from .ast import TemplateNode, TextNode, IdentNode, CallNode
from .tokenizer import Tokenizer
from .parser import Parser
from .exceptions import MapResError, MissingKeyError


class EvaluationError(MapResError):
    pass


class Evaluator:
    def __init__(self, layerstack, ctx=None):
        self.layerstack = layerstack
        self.ctx = ctx or {}
        self._seen = set()  # cycle detection

    # public api
    def evaluate(self, node):
        return self._eval(node)

    # internal dispatch
    def _eval(self, node):
        if isinstance(node, TemplateNode):
            return self._eval_template(node)

        if isinstance(node, TextNode):
            return node.text

        if isinstance(node, IdentNode):
            return self._eval_ident(node)

        if isinstance(node, CallNode):
            return self._eval_call(node)

        raise EvaluationError(f'Unknown AST node: {node}')

    # template
    def _eval_template(self, node: TemplateNode):
        parts = []
        for child in node.children:
            parts.append(self._eval(child))
        out = ''.join(parts)

        # recursion over full template output
        if self._has_recursive_maps():
            seen = set()
            depth = 0
            max_depth = self._get_max_depth()

            while depth < max_depth:
                new_out = self._re_resolve(out)
                if new_out == out:
                    break
                if new_out in seen:
                    raise EvaluationError('Cycle detected in template recursion')
                seen.add(new_out)
                out = new_out
                depth += 1

        return out

    # identifier
    def _eval_ident(self, node: IdentNode):
        name = node.name

        # ignore_delimiters: treat token as literal for this syntax
        if self._syntax_ignores_delimiters(node.syntax):
            return self._literal_from_syntax(name, node.syntax)

        # cycle detection
        if name in self._seen:
            raise EvaluationError(f"Cycle detected in identifier '{name}'")
        self._seen.add(name)

        parts = name.split('.')

        # 1. ctx first
        val = self._lookup_hierarchical(self.ctx, parts)
        if val is not None:
            self._seen.remove(name)
            return str(val)

        # 2. syntax-bound maps
        for m in self.layerstack.all_maps():
            if getattr(m, '__syntax__', None) not in (None, node.syntax):
                continue

            d = self._map_to_dict(m)
            val = self._lookup_hierarchical(d, parts)
            if val is not None:
                self._seen.remove(name)
                return str(val)

        self._seen.remove(name)
        raise MissingKeyError(name)

    # call (nested token)
    def _eval_call(self, node: CallNode):
        outer = node.name

        # ignore_delimiters: treat call token as literal
        if self._syntax_ignores_delimiters(node.syntax):
            arg_text = self._eval(node.arg)
            return self._literal_from_syntax(outer, node.syntax, is_call=True, arg_text=arg_text)

        if outer in self._seen:
            raise EvaluationError(f"Cycle detected in call '{outer}'")
        self._seen.add(outer)

        arg_value = self._eval(node.arg)
        parts = [outer, arg_value]

        # ctx first
        val = self._lookup_hierarchical(self.ctx, parts)
        if val is not None:
            self._seen.remove(outer)
            return str(val)

        # syntax-bound maps
        for m in self.layerstack.all_maps():
            if getattr(m, '__syntax__', None) not in (None, node.syntax):
                continue

            d = self._map_to_dict(m)
            val = self._lookup_hierarchical(d, parts)
            if val is not None:
                self._seen.remove(outer)
                return str(val)

        self._seen.remove(outer)
        raise MissingKeyError(f'{outer}({arg_value})')

    # helpers
    def _map_to_dict(self, m):
        if hasattr(m, 'as_map'):
            return m.as_map()
        if isinstance(m, dict):
            return m
        raise EvaluationError(f'Invalid map object: {m}')

    def _lookup_hierarchical(self, root, parts):
        cur = root
        for p in parts:
            if not isinstance(cur, dict):
                return None
            if p not in cur:
                return None
            cur = cur[p]
        return cur

    def _has_recursive_maps(self):
        for m in self.layerstack.all_maps():
            if getattr(m, '__recursive__', False):
                return True
        return False

    def _get_max_depth(self):
        depths = [
            getattr(m, '__max_depth__', 10)
            for m in self.layerstack.all_maps()
            if getattr(m, '__recursive__', False)
        ]
        return max(depths) if depths else 0

    def _re_resolve(self, text: str) -> str:
        tokens = Tokenizer(text).tokenize()
        ast = Parser(tokens).parse()
        return self.evaluate(ast)

    def _syntax_ignores_delimiters(self, syntax_name: str) -> bool:
        for m in self.layerstack.all_maps():
            if getattr(m, '__syntax__', None) == syntax_name:
                if getattr(m, '__ignore_delimiters__', False):
                    return True
        return False

    def _literal_from_syntax(self, name: str, syntax_name: str, is_call: bool = False, arg_text: str | None = None) -> str:
        if not is_call:
            if syntax_name == 'colons':
                return f':{name}:'
            if syntax_name == 'braces':
                return f'{{{{{name}}}}}'
            if syntax_name == 'dollars':
                return f'${{{name}}}'
            if syntax_name == 'angles':
                return f'<{name}>'
            if syntax_name == 'pipes':
                return f'|{name}|'
            if syntax_name == 'percents':
                return f'%{name}%'
            if syntax_name == 'paren_dollars':
                return f'$({name})'
            if syntax_name == 'at_tags':
                return f'@{name}@'
            if syntax_name == 'hash_tags':
                return f'#{name}#'
            return name

        # call literal: syntax-specific wrapping of name(arg_text)
        arg = arg_text or ''
        inner = f'{name}({arg})'

        if syntax_name == 'colons':
            return f':{inner}:'
        if syntax_name == 'braces':
            return f'{{{{{inner}}}}}'
        if syntax_name == 'dollars':
            return f'${{{inner}}}'
        if syntax_name == 'angles':
            return f'<{inner}>'
        if syntax_name == 'pipes':
            return f'|{inner}|'
        if syntax_name == 'percents':
            return f'%{inner}%'
        if syntax_name == 'paren_dollars':
            return f'$({inner})'
        if syntax_name == 'at_tags':
            return f'@{inner}@'
        if syntax_name == 'hash_tags':
            return f'#{inner}#'
        return inner
