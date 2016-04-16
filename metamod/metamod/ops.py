"ops.py -- commands on tables"

import collections
from . import row

WILDCARD = '%s'

class UnkFieldError(row.MetamodError):
    def __init__(self, rowclass, field):
        self.rowclass = rowclass
        self.field = field

    def __repr__(self):
        return '<%s %s %s>' % (self.__class__.__name__, rowclass, field)

class ColumnSpec:
    "this is used for unpacking columns from multi-table queries"
    def __init__(self, *pairs):
        """pairs is list of tuples like (model_class, column_name).
        supports *.
        None instead of a pair means skip that field.
        """
        self.pairs = []
        for pair in pairs:
            if pair is None: # none means skip
                self.pairs.append(None)
                continue
            rowclass, name = pair
            if name == '*':
                self.pairs.extend((rowclass, field.name) for field in rowclass.FIELDS)
            elif name in rowclass.__slots__:
                self.pairs.append(pair)
            else:
                raise UnkFieldError(rowclass, name)
        
        self.classes = collections.defaultdict(list)
        class_order = collections.OrderedDict()
        for i, pair in enumerate(self.pairs):
            if pair is None:
                continue
            rowclass, field = pair
            class_order[rowclass] = True
            self.classes[rowclass].append((field, i))
        self.class_order = class_order.keys()

    def readrow(self, row_):
        return [
            # warning: this has to be slow. maybe save slot index instead of slot name
            rowclass(**{field: row_[i] for field, i in self.classes[rowclass]})
            for rowclass in self.class_order
        ]

    def itermodels(self, cursor):
        for row_ in cursor:
            yield self.readrow(row_)

def insert(row_, returning=None, rawfields={}, wildcard=WILDCARD):
    "returning is a string of valid SQL. raw is for fields that should not be escaped (i.e. SQL expressions)"
    fields = collections.OrderedDict(
        (name, getattr(row_, name))
        for name in row_.__slots__ if getattr(row_, name) is not row.Missing
    )
    fields.update(rawfields)
    stmt = 'insert into %s (%s) values (%s)' % (
        row_.__table__(),
        ','.join(fields),
        ','.join(
            v if k in rawfields else wildcard
            for k,v in fields.items()
        )
    )
    if returning:
        stmt += ' returning %s' % ','.join(returning)
    return stmt, [v for k,v in fields.items() if k not in rawfields]

def whereclause(where, wildcard):
    return ' where %s' % ' and '.join('%s=%s' % (k, wildcard) for k in where)

def select_eq(rowclass, where, fields=('*',), for_update=False, limit=None, order=None, wildcard=WILDCARD):
    "simple select where all where clauses are ==. for more complicated selects, build them yourself"
    stmt = 'select %s from %s' % (','.join(fields), rowclass.__table__())
    if where:
        stmt += whereclause(where, wildcard)
    if order is not None:
        stmt += 'order by %s' % order
    if limit is not None:
        stmt += ' limit %i' % limit
    if for_update:
        stmt += ' for update'
    return stmt, where.values()

def pkey(rowclass, values):
    "return a where-dict for the rowclass given values"
    if len(rowclass.PKEY) != len(values):
        raise ValueError('length mismatch', rowclass.PKEY, values)
    return dict(zip(rowclass.PKEY, values))

def itermodels(cursor, rowclass):
    "assuming the cursor is primed with 'select *', iterate rowclass objects"
    for row_ in cursor:
        yield rowclass(*row_)

def select_models(cursor, rowclass, where, **kwargs):
    if 'fields' in kwargs and kwargs['fields'] != ('*',):
        raise ValueError("don't pass fields into select_models()", kwargs['fields'])
    cursor.execute(*select_eq(rowclass, where, **kwargs))
    return list(itermodels(cursor, rowclass))

def get(cursor, rowclass, pkey_vals, **kwargs):
    "get by primary key. return list of models (should have len 0 or 1)"
    return select_models(cursor, rowclass, pkey(rowclass, pkey_vals), **kwargs)

TYPES = {
    int: 'int',
    str: 'text',
    unicode: 'text',
    float: 'float',
    list: 'array',
}

def enum_name(rowclass, field):
    return '"%s_%s"' % (rowclass.__table__(), field.name)

def field_string(rowclass, field):
    return '%s %s' % (
        field.name,
        field.type if isinstance(field.type, basestring)
            else enum_name(rowclass, field) if isinstance(field.type, set)
            else TYPES[field.type]
    )

def create_indexes(rowclass):
    return tuple(
        index.render(rowclass) if isinstance(index, row.Index) else index
        for index in rowclass.INDEXES
    )

def create_types(rowclass):
    "i.e. enums"
    return tuple(
        'CREATE TYPE %s AS ENUM (%s)' % (
            enum_name(rowclass, field),
            ','.join("'%s'" % val for val in field.type)
        )
        for field in rowclass.FIELDS if isinstance(field.type, set)
    )

def create_table(rowclass):
    "returns a tuple of statements to init the table (including create table, create index, and create type for enum)"
    columns = [field_string(rowclass, field) for field in rowclass.FIELDS]
    if rowclass.PKEY:
        columns.append('PRIMARY KEY (%s)' % ','.join(rowclass.PKEY))
    stmt = 'CREATE TABLE "%s" (%s)' % (rowclass.__table__(), ', '.join(columns))
    return create_types(rowclass) + (stmt,) + create_indexes(rowclass)

def init_db(schema):
    "returns list of statements that will init the DB"
    return sum(map(create_table, schema.values()), ())

def update_eq(rowclass, where, update, wildcard=WILDCARD):
    "simple updates where WHERE clauses are = and SETs are value-based (i.e. their values get escaped, can't be SQL exprs)"
    stmt = 'update %s set %s' % (rowclass.__table__(), ','.join('%s=%%s' % k for k in update))
    if where:
        stmt += whereclause(where, wildcard)
    return stmt, (update.values() + where.values())
