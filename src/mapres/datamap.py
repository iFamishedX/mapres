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
    __mode__: str | None = None # "dynamic", "config", "callable", or None
    __recursive__: bool = False
    __missing_key__: str = 'error'  # 'error', 'silent', 'placeholder'
    __ignore_delimiters__: bool = False

    def as_map(self):
        '''
        Convert datamap fields into a dictionary.
        If mode='dynamic', evaluate provider functions.

        Callable mode does NOT change as_map() behavior; methods are
        used by the evaluator, not exported as map entries.
        '''
        result = {}

        # dataclass fields
        for f in fields(self):
            if not f.init or f.name.startswith('__'):
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

        # nested classes > nested dicts
        for name, obj in self.__class__.__dict__.items():
            if name.startswith('__'):
                continue
            if isinstance(obj, type):
                result[name] = self._class_to_dict(obj)

        return result

    def _class_to_dict(self, cls):
        out = {}

        if is_dataclass(cls):
            dummy = cls()
            for f in fields(dummy):
                if not f.init:
                    continue
                out[f.name] = getattr(dummy, f.name)

        for name, obj in cls.__dict__.items():
            if name.startswith('__'):
                continue
            if isinstance(obj, type):
                out[name] = self._class_to_dict(obj)

        return out


def datamap(_cls=None, *, syntax=None, mode=None, recursive=None,
            missing_key=None, ignore_delimiters=None):

    def wrap(cls):
        cls.__syntax__ = syntax
        cls.__mode__ = mode
        cls.__recursive__ = recursive
        cls.__missing_key__ = missing_key or 'error'
        cls.__ignore_delimiters__ = ignore_delimiters or False

        namespace = dict(cls.__dict__)
        namespace['__dict__'] = {}
        rules_obj = namespace.get('rules', None)

        cls = type(cls.__name__, (DataMap,), namespace)

        if rules_obj is not None:
            setattr(cls, 'rules', rules_obj)

        return dataclass(frozen=False)(cls)

    if _cls is not None and isinstance(_cls, type):
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
        if _cls is not None and isinstance(_cls, type):
            return datamap(_cls, syntax=self._syntax)
        return datamap(syntax=self._syntax, **kwargs)

    @property
    def config(self):
        return datamap(syntax=self._syntax, mode='config')

    @property
    def dynamic(self):
        return datamap(syntax=self._syntax, mode='dynamic')

    @property
    def callable(self):
        return datamap(syntax=self._syntax, mode='callable')


datamap.braces        = _SyntaxFactory(syntax.braces)
datamap.dollars       = _SyntaxFactory(syntax.dollars)
datamap.angles        = _SyntaxFactory(syntax.angles)
datamap.percents      = _SyntaxFactory(syntax.percents)
datamap.pipes         = _SyntaxFactory(syntax.pipes)
datamap.colons        = _SyntaxFactory(syntax.colons)
datamap.at_tags       = _SyntaxFactory(syntax.at_tags)
datamap.hash_tags     = _SyntaxFactory(syntax.hash_tags)
datamap.paren_dollars = _SyntaxFactory(syntax.paren_dollars)

datamap.config   = datamap(mode='config')
datamap.dynamic  = datamap(mode='dynamic')
datamap.callable = datamap(mode='callable')
