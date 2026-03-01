class Test:
    x: int | None = None

import pprint
f = Test.__dict__['__annotate_func__']
print("format 1:", f(1))
print("format 2:", f(2))
