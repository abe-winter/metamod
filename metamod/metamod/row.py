"row.py -- "

import re, six
from . import stmt

class DuplicateTableError(StandardError): pass
class NArgsError(StandardError): pass

class Missing:
    "empty class for distinguishing 'missing' from intentional null"

class Index:
    "helper for indexes, not mandatory"
    def __init__(self, fields, method=None, where=None, unique=False):
        self.fields, self.method, self.where, self.unique = fields, method, where, unique

    def render(self, rowclass):
        return stmt.SPACE.join(
            'CREATE',
            stmt.Cond('UNIQUE', self.unique),
            'INDEX',
            stmt.Prefixed('ON', stmt.Quoted(rowclass.__table__())),
            stmt.Prefixed('USING', self.method),
            stmt.ParenList(self.fields),
            stmt.Prefixed('WHERE', self.where)
        )

class Field:
    def __init__(self, name, type=None):
        self.name, self.type = name, type

def classname2tablename(classname):
    "this does a camelcase manipulation -- expect edge cases, this isn't algebraic"
    tokens = re.findall('([A-Z][a-z0-9]*)', classname)
    return '_'.join(tok.lower() for tok in tokens)

def cast_fields(list_):
    "takes list of Field or tuple. returns list of Field (using tuples as constructor arguments)"
    return [
        field if isinstance(field, Field) else Field(*field)
        for field in list_
    ]

class RowMeta(type):
    "this sets __slots__ on RowBase descendants and adds class to SCHEMA"
    def __new__(class_, name, parents, dict_):
        dict_['FIELDS'] = cast_fields(dict_['FIELDS'])
        names = tuple(f.name for f in dict_['FIELDS'])
        dict_['__slots__'] = names
        tablename = classname2tablename(name)
        newchild = super(RowMeta, class_).__new__(class_, name, parents, dict_)
        if dict_['SCHEMA'] is not None:
            if tablename in dict_['SCHEMA']:
                raise DuplicateTableError(tablename, dict_['SCHEMA'][tablename].__module__)
            dict_['SCHEMA'][tablename] = newchild
        return newchild

@six.add_metaclass(RowMeta)
class RowBase(object):
    FIELDS = () # list of Field *or* of tuple (name, type) which get fed to cast_fields
    SCHEMA = None
    PKEY = () # list of strings (field names)
    INDEXES = () # list of strings (whole statements)
    __slots__ = () # careful: without this, descendant classes won't enforce slots
  
    def __init__(self, *args, **kwargs):
        if len(args) > len(self.__slots__):
            raise NArgsError('too many args', len(args), len(self.__slots__))
        names_set = []
        for name, val in zip(self.__slots__, args):
            names_set.append(name)
            setattr(self, name, val)
        for name, val in kwargs.items():
            if name in names_set:
                raise ValueError('arg %r already specified in position %i' % (name, self.__slots__.index(name)))
            names_set.append(name)
            setattr(self, name, val)
        for name in self.__slots__:
            if name not in names_set:
                setattr(self, name, Missing)

    def __pkey__(self):
        return tuple(getattr(self, field) for field in self.PKEY)

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            ' '.join('%s=%s' % (name, getattr(self, name)) for name in self.__slots__)
        )

    @classmethod
    def __table__(class_):
        return classname2tablename(class_.__name__)
