from __future__ import print_function
import functools
import traceback
import sys

INDENT = 4*' '

def stacktrace(func):
    @functools.wraps(func)
    def wrapped(*args, **kwds):
        # Get all but last line returned by traceback.format_stack()
        # which is the line below.
        callstack = '\n'.join([INDENT+line.strip() for line in traceback.format_stack()][:-1])
        print('{}() called:'.format(func.__name__))
        print(callstack)
        return func(*args, **kwds)

    return wrapped

#@stacktrace
def fact(n: int) -> int: 
    if n == 1: 
        return n
    else: 
        #for line in traceback.format_stack():
        #    print(line.strip())
        return n*fact(n-1)

print(fact(5))