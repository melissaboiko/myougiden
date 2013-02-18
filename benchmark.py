#!/usr/bin/env python3
import timeit
import subprocess
import builtins

devnull = open('/dev/null', 'w')

def call(*args):
    subprocess.call(args, stdout=devnull)

# low ent_seq
def quicksearch1():
    call('./myougiden.py',
         '-e', 'whole',
         '--reading',
         '--output-mode', 'tab',
         'ヽ')

# high ent_seq
def quicksearch2():
    call('./myougiden.py',
         '-e', 'whole',
         '--kanji',
         '--output-mode', 'tab',
         '首鼠')

def quicksearch3():
    call('./myougiden.py',
         '-e', 'whole',
         '--sense',
         '--output-mode', 'tab',
         'acetylcellulose')

# try to guess everything and fail
def slowsearch1():
    call('./myougiden.py',
         '-e', 'auto',
         '--output-mode', 'human',
         '亞衣有会尾')

def slowsearch2():
    call('./myougiden.py',
         '-x',
         '-e', 'auto',
         '--output-mode', 'human',
         '亞衣有会尾')

# sometimes non-regexp word search seems especially slow
def slowsearch3():
    call('./myougiden.py',
         '-e', 'auto',
         '--output-mode', 'human',
         'word')


# dummy searches to cache db in filesystem
for i in (1,2,3):
    quicksearch1()
    quicksearch2()
    quicksearch3()

# whee
builtins.__dict__.update(locals())

# about the reason for using min(), see
# http://docs.python.org/3/library/timeit.html#timeit.Timer.repeat
quick = []
quick.append(min(timeit.repeat('quicksearch1()', repeat=5, number=1)))
quick.append(min(timeit.repeat('quicksearch2()', repeat=5, number=1)))
quick.append(min(timeit.repeat('quicksearch3()', repeat=5, number=1)))

slow = []
slow.append(min(timeit.repeat('slowsearch1()', repeat=5, number=1)))
slow.append(min(timeit.repeat('slowsearch2()', repeat=5, number=1)))
slow.append(min(timeit.repeat('slowsearch3()', repeat=5, number=1)))

print('Quick: ', quick)
print('Slow: ', slow)
