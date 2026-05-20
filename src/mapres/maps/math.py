import ast
from mapres.datamap import datamap, syntax


def safe_eval(expr: str, ctx: dict):
    """
    Safely evaluate arithmetic expressions using AST.
    Allowed:
      - numbers
      - names (from ctx)
      - + - * / // % **
      - parentheses
    """
    node = ast.parse(expr, mode="eval")

    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp,
        ast.Num, ast.Name, ast.Load,
        ast.Add, ast.Sub, ast.Mult, ast.Div,
        ast.FloorDiv, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd, ast.Constant,
    )

    for sub in ast.walk(node):
        if not isinstance(sub, allowed_nodes):
            raise ValueError(f"Disallowed expression: {expr}")

        if isinstance(sub, ast.Name) and sub.id not in ctx:
            raise KeyError(f"Unknown variable '{sub.id}' in expression '{expr}'")

    return eval(compile(node, "<math>", "eval"), {}, ctx)


@datamap(syntax=r"\$\{\{(.+?)\}\}", mode="dynamic")
class MathMap:
    expr: str = None

    def __init__(self):
        self._ctx = {}

    @property
    def providers(self):
        return {
            "expr": lambda: None
        }

    def get_map(self, ctx, resolver):
        # store ctx so safe_eval can use it
        self._ctx = ctx

        def repl(expr):
            return safe_eval(expr, ctx)

        return repl


# proxy map
math = MathMap