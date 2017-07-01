from __future__ import print_function
import six, pytest
from metamod import row

@pytest.fixture()
def SCHEMA():
  return {}

@pytest.fixture()
def ABRow(SCHEMA):
  schema = SCHEMA
  class ABRow(row.RowBase):
    FIELDS = [('a', int), ('b', int)]
    # warning: without the schema rename, this is a function. what's happening? easter egg in the scoping spec?
    SCHEMA = schema
    PKEY = ('a',)
    INDEXES = [
      'create index on "a_b_row" (a,b)',
      row.Index(('a','b'), 'gist')
    ]
  return ABRow

@pytest.fixture()
def ACRow(SCHEMA):
    schema = SCHEMA
    class ACRow(row.RowBase):
        FIELDS = [('a', int), ('c', int)]
        SCHEMA = schema
        PKEY = ('a',)
    return ACRow

def test_field_attrs(ABRow):
  r = ABRow(1,2)
  assert r.a == 1 and r.b == 2
  print(r.__slots__)
  with pytest.raises(AttributeError):
    r.c = 10

def test_ctor_styles(ABRow):
  rows = [
    ABRow(1,2),
    ABRow(1, b=2),
    ABRow(a=1, b=2),
  ]
  assert all(r.a == 1 and r.b == 2 for r in rows)
  r = ABRow(1)
  assert r.a == 1 and r.b is row.Missing
  with pytest.raises(row.NArgsError):
    r5 = ABRow(1, 2, 3)
  with pytest.raises(AttributeError):
    r6 = ABRow(a=1, c=3)

def test_dupe_schema(ABRow):
  with pytest.raises(row.DuplicateTableError):
    class ABRow(row.RowBase):
      FIELDS = []
      SCHEMA = ABRow.SCHEMA

def test_eq(ABRow):
  assert ABRow('a', 'b') == ABRow('a', 'b')
  assert ABRow('a', 'b') != ABRow('a', 'b2')
