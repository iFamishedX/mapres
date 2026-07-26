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


# main decorator factory
def datamap(_cls=None, *, syntax=syntax.double_braces, mode=None):
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

    # direct decorator: @datamap(...)
    if _cls is not None:
        return wrap(_cls)

    # factory: @datamap(...)
    return wrap


# syntax-bound decorator factories
class _SyntaxFactory:
    def __init__(self, syntax_value):
        self._syntax = syntax_value

    def __call__(self, **kwargs):
        # allows: @datamap.double_braces(mode='config')
        return datamap(syntax=self._syntax, **kwargs)

    @property
    def config(self):
        # allows: @datamap.double_braces.config
        return datamap(syntax=self._syntax, mode='config')


# build syntax shortcuts
datamap.double_braces = _SyntaxFactory(syntax.double_braces)
datamap.angles        = _SyntaxFactory(syntax.angles)
datamap.dollars       = _SyntaxFactory(syntax.dollars)
datamap.percents      = _SyntaxFactory(syntax.percents)
datamap.at_tags       = _SyntaxFactory(syntax.at_tags)
datamap.hash_tags     = _SyntaxFactory(syntax.hash_tags)
datamap.pipe_tags     = _SyntaxFactory(syntax.pipe_tags)
datamap.paren_dollar  = _SyntaxFactory(syntax.paren_dollar)
datamap.colons        = _SyntaxFactory(syntax.colons)

# global mode shortcut
datamap.config = datamap(mode='config')
