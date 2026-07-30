from .ast import TemplateNode, TextNode, IdentNode, CallNode


class EvaluationError(Exception):
    pass


class Evaluator:
    def __init__(self, layerstack, ctx=None):
        self.layerstack = layerstack
        self.ctx = ctx or {}
        self._seen = set()  # cycle detection

    # -----------------------------
    # PUBLIC API
    # -----------------------------
    def evaluate(self, node):
        return self._eval(node)

    # -----------------------------
    # INTERNAL DISPATCH
    # -----------------------------
    def _eval(self, node):
        if isinstance(node, TemplateNode):
            return self._eval_template(node)

        if isinstance(node, TextNode):
            return node.text

        if isinstance(node, IdentNode):
            return self._eval_ident(node)

        if isinstance(node, CallNode):
            return self._eval_call(node)

        raise EvaluationError(f"Unknown AST node: {node}")

    # -----------------------------
    # TEMPLATE
    # -----------------------------
    def _eval_template(self, node: TemplateNode):
        parts = []
        for child in node.children:
            parts.append(self._eval(child))
        return "".join(parts)

    # -----------------------------
    # IDENTIFIER
    # -----------------------------
    def _eval_ident(self, node: IdentNode):
        name = node.name

        # cycle detection
        if name in self._seen:
            raise EvaluationError(f"Cycle detected in identifier '{name}'")
        self._seen.add(name)

        parts = name.split(".")

        # 1. ctx first
        val = self._lookup_hierarchical(self.ctx, parts)
        if val is not None:
            self._seen.remove(name)
            return str(val)

        # 2. syntax-bound maps
        for m in self.layerstack.all_maps():
            if getattr(m, "__syntax__", None) not in (None, node.syntax):
                continue

            d = self._map_to_dict(m)
            val = self._lookup_hierarchical(d, parts)
            if val is not None:
                self._seen.remove(name)
                return str(val)

        self._seen.remove(name)
        raise EvaluationError(f"Missing key '{name}'")

    # -----------------------------
    # CALL (nested token)
    # -----------------------------
    def _eval_call(self, node: CallNode):
        outer = node.name

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
            if getattr(m, "__syntax__", None) not in (None, node.syntax):
                continue

            d = self._map_to_dict(m)
            val = self._lookup_hierarchical(d, parts)
            if val is not None:
                self._seen.remove(outer)
                return str(val)

        self._seen.remove(outer)
        raise EvaluationError(f"Missing nested key '{outer}({arg_value})'")

    # -----------------------------
    # HELPERS
    # -----------------------------
    def _map_to_dict(self, m):
        if hasattr(m, "as_map"):
            return m.as_map()
        if isinstance(m, dict):
            return m
        raise EvaluationError(f"Invalid map object: {m}")

    def _lookup_hierarchical(self, root, parts):
        cur = root
        for p in parts:
            if not isinstance(cur, dict):
                return None
            if p not in cur:
                return None
            cur = cur[p]
        return cur
