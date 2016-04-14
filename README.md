## metamod package (python)

- [overview](#overview)
- [vs other ORMs](#vs-other-orms)
- [example](#example)
- [roadmap](#roadmap)

### overview

metamod stands for 'metaclass models'.

* lightweight ORM (about 200 lines)
* uses python's `__slots__` so instances are lightweight and classes are self-documenting

### vs other ORMs

The goal here is to be a thin layer on SQL. We want to wrap simple, well-understood and often-repeated actions like:
* create table
* insert
* simple select statements (where field=value)

Database writes are emitted as raw SQL that you can pass to a cursor. Database reads operate on a cursor (but *not* on a connection; you manage your connections yourself).

We don't want to:
* generate complex SQL statements, especially for joins
* provide any type conversions (adapt / mogrify); we'll trust psycopg2 or pymysql for that
* normalize behavior across different DBs
* hide connections & pooling behind classes

### example

```python
import sys
from metamod import row, ops

class ABRow(row.RowBase):
    SCHEMA = None # not required to bind to a schema
    FIELDS = [('a', int), ('b', int)]
    PKEY = ('a',)
    INDEXES = [
        'create index on "a_b_row" (a,b)',
        row.Index(('a','b'), 'gist')
    ]

# smart-ish contructor
row1 = ABRow(1, 2)
row2 = ABRow(a=1, b=2)
row3 = ABRow(1, b=2)

# ABRow is a new-style class with slots
assert ABRow.__slots__ == ('a', 'b')
sys.getsizeof(row1) # 64 bytes, way smaller than a non-slots class with a __dict__

# attribute access
assert row1.a == 1

# ops.insert produces sql & params that can be passed to a DBAPI2 cursor
assert ops.insert(row1) == (
    'insert into a_b_row (a,b) values (%s,%s)',
    [1, 2]
)

from somewhere import db_connect
with db_connect() as con, con, con as cursor:
    cursor.execute(*ops.insert(row1))
    models = select_models(cursor, ABRow, {'a':1})

assert models[0].a == 1
```

### roadmap

* support null constraints and relations (i.e. foreign keys), use that to support factories in test
* pylint plugin for static-checking DB field use
* delta against existing DDL for migrations? (maybe)
