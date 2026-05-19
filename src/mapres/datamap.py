import re
from dataclasses import dataclass, fields, is_dataclass
from .syntax import Syntax

@dataclass
class DataMap:
    '''Core datamap class. Contains logic used to make datamaps'''
    __syntax__: str = Syntax.braces
    __mode__ = None

    def as_map(self):
        result = {}

        for f in fields(self):
            if not f.init or f.name in ("__syntax__", "__mode__"):
                continue

            val = getattr(self, f.name)

            # dynamic mode
            if self.__mode__ == "dynamic":
                providers = getattr(self, "providers", None)

                # explicit provider dict only
                if isinstance(providers, dict) and f.name in providers:
                    val = providers[f.name]

                # callables are executed
                if callable(val):
                    val = val()

            result[f.name] = val

        return result

    @classmethod
    def get_syntax(cls):
        return getattr(cls, "__syntax__", Syntax.braces)

# decorator
def datamap(
    _cls = None,
    *,
    syntax: str = Syntax.braces,
    mode: bool | None = None,
):
    '''@datamap decorator with optional values'''
    def wrap(cls):
        cls.__syntax__ = syntax
        cls.__mode__ = mode

        namespace = dict(cls.__dict__)
        namespace["__dict__"] = {}

        cls = type(cls.__name__, (DataMap,), namespace)
        return dataclass(frozen=False)(cls)

    return wrap if _cls is None else wrap(_cls)

# decorator shortcuts
datamap.braces = datamap(syntax=Syntax.braces)
datamap.angles = datamap(syntax=Syntax.angles)
datamap.dollars = datamap(syntax=Syntax.dollars)
datamap.percents = datamap(syntax=Syntax.percents)
