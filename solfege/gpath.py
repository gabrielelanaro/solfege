
from __future__ import absolute_import
class Path(tuple):
    def first(self):
        v = list(self)
        v[-1] = 0
        return Path(v)
    def next(self):
        v = list(self)
        v[-1] += 1
        return Path(v)
    def prev(self):
        v = list(self)
        v[-1] -= 1
        return Path(v)
    def child(self):
        v = list(self)
        v.append(0)
        return Path(v)
    def parent(self):
        v = list(self)
        v = v[:-1]
        return Path(v)


