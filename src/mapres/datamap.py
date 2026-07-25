import re
from dataclasses import dataclass, fields, is_dataclass

class syntax:
    double_braces = r'\{\{([^{}]+)\}\}'     # {{value}}
    dollars       = r'\$\{([^{}]+)\}'       # ${value}
    angles        = r'<([^<>]+)>'           # <value>
    percents      = r'%([^%]+)%'            # %value%
    at_tags       = r'@([^@]+)@'            # @value@
    hash_tags     = r'#([^#]+)#'            # #value#
    pipe_tags     = r'\|([^|]+)\|'          # |value|
    paren_dollar  = r'\$\(([^)]+)\)'        # $(value)
    colons        = r':([^:\n]+):'          # :value:

@dataclass
class DataMap:
    '''Core datamap class. Contains logic used to make datamaps'''
    __syntax__: str = syntax.double_braces
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
        return getattr(cls, '__syntax__', syntax.double_braces)


# decorator
def datamap(
    _cls = None,
    *,
    syntax: str = syntax.double_braces,
    mode: bool | str | None = None,
):
    '''@datamap decorator with optional values'''
    def wrap(cls):
        cls.__syntax__ = syntax
        cls.__mode__ = mode
        namespace = dict(cls.__dict__)
        namespace['__dict__'] = {}
        rules_obj = namespace.get('rules', None)
        cls = type(cls.__name__, (DataMap,), namespace)
        if rules_obj is not None:
            setattr(cls, 'rules', rules_obj)
        return dataclass(frozen=False)(cls)
    return wrap if _cls is None else wrap(_cls)


# decorator shortcuts
datamap.double_braces = datamap(syntax=syntax.double_braces)
datamap.angles        = datamap(syntax=syntax.angles)
datamap.dollars       = datamap(syntax=syntax.dollars)
datamap.percents      = datamap(syntax=syntax.percents)
datamap.at_tags       = datamap(syntax=syntax.at_tags)
datamap.hash_tags     = datamap(syntax=syntax.hash_tags)
datamap.pipe_tags     = datamap(syntax=syntax.pipe_tags)
datamap.paren_dollar  = datamap(syntax=syntax.paren_dollar)
datamap.colons        = datamap(syntax=syntax.colons)
