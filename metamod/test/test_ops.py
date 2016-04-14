import six
from metamod import ops, row
from test_row import ABRow, SCHEMA

def test_insert(ABRow):
  row = ABRow(1,3)
  assert ops.insert(row) == (
    'insert into a_b_row (a,b) values (%s,%s)',
    [1, 3]
  )
  assert ops.insert(row, returning=('a')) == (
    'insert into a_b_row (a,b) values (%s,%s) returning a',
    [1, 3]
  )

def test_insert_literal(ABRow):
  row = ABRow(1,3)
  expr = 'select max(id)+1 from T'
  assert ops.insert(row, rawfields={'userid':expr}) == (
    'insert into a_b_row (a,b,userid) values (%%s,%%s,%s)' % expr,
    [1, 3]
  )

def test_insert_array(ABRow):
  "make sure sql handling does something that works for psycopg2"
  row = ABRow(1, [3,4,5])
  assert ops.insert(row)[1] == [1, [3,4,5]]

def test_select_eq(ABRow):
  assert ops.select_eq(ABRow, {}) == (
    'select * from a_b_row',
    []
  )
  assert ops.select_eq(ABRow, {'a':3}) == (
    'select * from a_b_row where a=%s',
    [3]
  )
  assert ops.select_eq(ABRow, {'a':3, 'b':2}, ('a','b')) == (
    'select a,b from a_b_row where a=%s and b=%s',
    [3, 2]
  )

def test_create_table(ABRow):
  assert ops.init_db(ABRow.SCHEMA) \
    == ops.create_table(ABRow) \
    == (
      'CREATE TABLE "a_b_row" (a int, b int, PRIMARY KEY (a))',
      'create index on "a_b_row" (a,b)',
      'CREATE INDEX ON "a_b_row" USING gist (a,b)',
    )

def test_update(ABRow):
  assert ops.update_eq(ABRow, {'a':3}, {'b':5}) == (
    'update a_b_row set b=%s where a=%s',
    [5, 3]
  )
