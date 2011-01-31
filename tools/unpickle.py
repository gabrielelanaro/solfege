#!/usr/bin/python

import pickle
import pprint
import sys
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

renametable = {
    'src.dataparser': 'solfege.dataparser',
    }

def mapname(name):
    if name in renametable:
        return renametable[name]
    return name

def mapped_load_global(self):
    module = mapname(self.readline()[:-1])
    name = mapname(self.readline()[:-1])
    klass = self.find_class(module, name)
    self.append(klass)

def loads(file):
    unpickler = pickle.Unpickler(file)
    unpickler.dispatch[pickle.GLOBAL] = mapped_load_global
    return unpickler.load() 

print sys.argv
f = file(sys.argv[1], 'r')
d = loads(f)
f.close()
pprint.pprint(d)
