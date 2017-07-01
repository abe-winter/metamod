"""stmt.py -- helper for constructing string statements with some keyword stuff going on.
sqlbuilder may also do this, in which case switch over.
"""

import six

def render(field_or_string):
    return field_or_string if isinstance(field_or_string, six.string_types) else field_or_string.render()

class Delim:
    "top-level joiner. a more advanced version of this could have sorting rules"
    def __init__(self, delim):
        self.delim = delim

    def join(self, *fields):
        return self.delim.join(filter(None, map(render, fields)))

SPACE = Delim(' ')

class StmtField(object):
    "base"
    def render(self):
        raise NotImplementedError("implement render in child class")

class ParenList(StmtField):
    def __init__(self, tokens):
        self.tokens = tokens

    def render(self):
        return '(%s)' % ','.join(map(render, self.tokens))

class Quoted(StmtField):
    def __init__(self, val):
        self.val = val

    def render(self):
        if '"' in self.val:
            raise ValueError("don't know how to escape in Quoted StmtField", self.val)
        return '"%s"' % self.val

class Prefixed(StmtField):
    def __init__(self, prefix, val):
        self.prefix, self.val = prefix, val

    def render(self):
        return '%s %s' % tuple(map(render, (self.prefix, self.val))) if self.val else None

class Cond(StmtField):
    def __init__(self, display, cond):
        self.display, self.cond = display, cond

    def render(self):
        return self.cond and self.display
