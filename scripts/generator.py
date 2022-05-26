#!/usr/bin/env python3
# coding: utf-8

# TODO: come up with something better
# when i feel like doing so

import sys

FILE_HEADER = '''\
# coding: utf-8

from abc import ABC, abstractmethod

class {0}:
    pass
'''

ASSGN_TEMPLATE = ' ' * 8 + 'self.{0} = {0}'
CLASS_TEMPLATE = '''\
class {0}({1}):
    def __init__(self, {2}):
{3}

    def accept(self, visitor):
        return visitor.visit_{4}_{5}(self)
\
'''

VISITOR_TEMPLATE = '''\
class {0}Visitor(ABC):
{1}\
'''
VISIT_TEMPLATE = '''\
    @abstractmethod
    def visit_{0}_{1}(self, {1}):
        pass
'''

def generate_class(cname, name, *fields):
    params = ', '.join(f for f in fields)
    fields = '\n'.join(ASSGN_TEMPLATE.format(f) for f in fields)

    return CLASS_TEMPLATE.format(name, cname, params, fields, name.lower(), cname.lower())

def generate_file(cname, data):
    visits = '\n'.join(VISIT_TEMPLATE.format(e.lower(), cname.lower()) for e, *_ in data)

    print(
        FILE_HEADER.format(cname) + '\n' + \
        VISITOR_TEMPLATE.format(cname, visits) + '\n' + \
        '\n'.join(generate_class(cname, n, *f) for n, *f in data), end='')

def main():
    if len(sys.argv) < 2:
        exit(1)

    exprs = (
        'Expr',
        [
            ['Binary', 'lt', 'op', 'rt'],
            ['Grouping', 'expression'],
            ['Literal', 'value'],
            ['Unary', 'op', 'expression'],
            ['Variable', 'name']
        ]
    )

    stmts = (
        'Stmt',
        [
            ['Expression', 'expression'],
            ['Print', 'expression'],
            ['Var', 'name', 'initializer'],
        ]
    )

    match sys.argv[1]:
        case 'exprs': generate_file(*exprs)
        case 'stmts': generate_file(*stmts)

if __name__ == '__main__':
    main()
