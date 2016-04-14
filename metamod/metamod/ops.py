"ops.py -- commands on tables"

import collections
from . import row

def insert(row_, returning=None, rawfields={}):
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
            v if k in rawfields else '%s'
            for k,v in fields.items()
        )
    )
    if returning:
        stmt += ' returning %s' % ','.join(returning)
    return stmt, [v for k,v in fields.items() if k not in rawfields]

def whereclause(where):
    return ' where %s' % ' and '.join('%s=%%s' % k for k in where)

def select_eq(rowclass, where, fields=('*',), for_update=False, limit=None, order=None):
    "simple select where all where clauses are ==. for more complicated selects, build them yourself"
    stmt = 'select %s from %s' % (','.join(fields), rowclass.__table__())
    if where:
        stmt += whereclause(where)
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

def select_models(cursor, rowclass, where, **kwargs):
    if 'fields' in kwargs and kwargs['fields'] != ('*',):
        raise ValueError("don't pass fields into select_models()", kwargs['fields'])
    cursor.execute(*select_eq(rowclass, where, **kwargs))
    return [
        rowclass(*vals)
        for vals in cursor
    ]

def get(cursor, rowclass, pkey_vals, **kwargs):
    "get by primary key. return "
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

def update_eq(rowclass, where, update):
    "simple updates where WHERE clauses are = and SETs are value-based (i.e. their values get escaped, can't be SQL exprs)"
    stmt = 'update %s set %s' % (rowclass.__table__(), ','.join('%s=%%s' % k for k in update))
    if where:
        stmt += whereclause(where)
    return stmt, (update.values() + where.values())
