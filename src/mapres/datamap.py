import re
from dataclasses import dataclass, fields, is_dataclass

# syntax identifiers
class syntax:
    braces         = 'braces'           # {{value}}
    dollars        = 'dollars'          # ${value}
    angles         = 'angles'           # <value>
    percents       = 'percents'         # %value%
    pipes          = 'pipes'            # |value|
    colons         = 'colons'           # :value:
    at_tags        = 'at_tags'          # @value@
    hash_tags      = 'hash_tags'        # #value#
    paren_dollars  = 'paren_dollars'    # $(value)


# base datamap class
@dataclass
class DataMap:
    '''
    Core datamap class for mapres 3.

    Responsibilities:
        - hold fields
        - optionally evaluate dynamic providers
        - return a dict via as_map()

    Syntax metadata (__syntax__) determines which delimiters
    this map responds to (angle, brace, colon, percent, pipe, etc).

    Mode metadata (__mode__) controls behavior:
        - None: plain static map
        - "dynamic": values may be provided by callables/providers
        - "config": config-style maps (no dynamic evaluation)
        - "callable": map exposes callable methods for nested calls
    '''
    __syntax__: str = None
    __mode__: str | None = None  # "dynamic", "config", "callable", or None

    def as_map(self):
        '''
        Convert datamap fields into a dictionary.
        If mode='dynamic', evaluate provider functions.

        Callable mode does NOT change as_map() behavior; methods are
        used by the evaluator, not exported as map entries.
        '''
        result = {}

        for f in fields(self):
            if not f.init or f.name in ('__syntax__', '__mode__'):
                continue

            val = getattr(self, f.name)

            # dynamic provider support
            if self.__mode__ == 'dynamic':
                providers = getattr(self, 'providers', None)
                if isinstance(providers, dict) and f.name in providers:
                    val = providers[f.name]
                if callable(val):
                    val = val()

            result[f.name] = val

        return result


# main decorator factory
def datamap(_cls=None, *, syntax=None, mode=None):
    '''@datamap decorator'''
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
    if _cls is not None:
        return wrap(_cls)
    return wrap


# syntax-bound decorator factories
class _SyntaxFactory:
    '''
    Allows:
        @datamap.angles
        @datamap.angles(mode='config')
        @datamap.angles.config
        @datamap.angles.dynamic
        @datamap.angles.callable
    '''
    def __init__(self, syntax_name):
        self._syntax = syntax_name

    def __call__(self, _cls=None, **kwargs):
        # Case 1: bare decorator: @datamap.angles
        if _cls is not None and isinstance(_cls, type):
            return datamap(_cls, syntax=self._syntax)

        # Case 2: decorator with args: @datamap.angles(mode='config')
        return datamap(syntax=self._syntax, **kwargs)

    @property
    def config(self):
        # Case 3: @datamap.angles.config
        return datamap(syntax=self._syntax, mode='config')

    @property
    def dynamic(self):
        # @datamap.angles.dynamic
        return datamap(syntax=self._syntax, mode='dynamic')

    @property
    def callable(self):
        # @datamap.angles.callable
        return datamap(syntax=self._syntax, mode='callable')


# build syntax shortcuts
datamap.braces        = _SyntaxFactory(syntax.braces)
datamap.dollars       = _SyntaxFactory(syntax.dollars)
datamap.angles        = _SyntaxFactory(syntax.angles)
datamap.percents      = _SyntaxFactory(syntax.percents)
datamap.pipes         = _SyntaxFactory(syntax.pipes)
datamap.colons        = _SyntaxFactory(syntax.colons)
datamap.at_tags       = _SyntaxFactory(syntax.at_tags)
datamap.hash_tags     = _SyntaxFactory(syntax.hash_tags)
datamap.paren_dollars = _SyntaxFactory(syntax.paren_dollars)

# global mode shortcuts
datamap.config   = datamap(mode='config')
datamap.dynamic  = datamap(mode='dynamic')
datamap.callable = datamap(mode='callable')
