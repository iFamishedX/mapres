import re
from dataclasses import dataclass, fields, is_dataclass

class syntax:
    braces   = r'\{([^{}]+)\}'
    dollars  = r'\$\{([^{}]+)\}'
    angles   = r'<([^<>]+)>'
    percents = r'%([^%]+)%'


@dataclass
class DataMap:
    '''Core datamap class. Contains logic used to make datamaps'''
    __syntax__: str = syntax.braces
    __mode__: str | None = None

    def as_map(self):
        result = {}
        for f in fields(self):
            if not f.init or f.name in ('__syntax__', '__mode__'):
                continue
            val = getattr(self, f.name)
            if self.__mode__ == 'dynamic':
                providers = getattr(self, 'providers', None)
                if isinstance(providers, dict) and f.name in providers:
                    val = providers[f.name]
                if callable(val):
                    val = val()
            result[f.name] = val
        return result

    @classmethod
    def get_syntax(cls):
        return getattr(cls, '__syntax__', syntax.braces)


# decorator
def datamap(
    _cls = None,
    *,
    syntax: str = syntax.braces,
    mode: bool | str | None = None,
):
    '''@datamap decorator with optional values'''
    def wrap(cls):
        cls.__syntax__ = syntax
        cls.__mode__ = mode
        namespace = dict(cls.__dict__)
        namespace['__dict__'] = {}
        # preserve any rules class defined in the original namespace by attaching it to the generated class
        rules_obj = namespace.get('rules', None)
        cls = type(cls.__name__, (DataMap,), namespace)
        # attach rules (if present) to the new class so validators can read them via the datamap class
        if rules_obj is not None:
            setattr(cls, 'rules', rules_obj)
        return dataclass(frozen=False)(cls)
    return wrap if _cls is None else wrap(_cls)


# decorator shortcuts
datamap.braces = datamap(syntax=syntax.braces)
datamap.angles = datamap(syntax=syntax.angles)
datamap.dollars = datamap(syntax=syntax.dollars)
datamap.percents = datamap(syntax=syntax.percents)
