# coding: utf-8

from pox.error import ParseError, build_parse_error
from pox.scanner import TokenType

from pox.parser.exprs import *
from pox.parser.stmts import *

SYNC_TOKENS = [
    TokenType.IF, TokenType.FOR, TokenType.LET,
    TokenType.FN, TokenType.WHILE, TokenType.CLASS, TokenType.RETURN]

class Parser:
    current = 0

    def __init__(self, tokens):
        self.tokens = tokens

    def peek(self):
        return self.tokens[self.current]

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def previous(self):
        return self.tokens[self.current - 1]

    def advance(self):
        if not self.is_at_end():
            self.current += 1

        return self.previous()

    def check(self, t):
        if self.is_at_end():
            return False

        return self.peek().type == t

    def match(self, *types):
        if matched := any(map(self.check, types)):
            self.advance()

        return matched

    def error(self, message):
        return ParseError(build_parse_error(self, message))

    def consume(self, t, message):
        if self.check(t):
            return self.advance()

        raise self.error(message)

    def synchronize(self):
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON or \
                    self.peek().type in SYNC_TOKENS:
                return

            self.advance()

    def parse(self, pox):
        statements = []

        while not self.is_at_end():
            try:
                statements.append(self.declaration())
            except ParseError as err:
                self.synchronize()
                pox.report_error(err)

        return statements

    def declaration(self):
        if self.match(TokenType.CLASS): return self.class_declaration()
        if self.match(TokenType.LET)  : return self.var_declaration()
        if self.match(TokenType.FN)   : return self.fn_declaration('function')

        return self.statement()

    def var_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, 'expect variable name')
        init = None

        if self.match(TokenType.EQUAL):
            init = self.expression()

        self.consume(TokenType.SEMICOLON, 'expect \';\' after variable declaration')
        return Let(name, init)

    def fn_declaration(self, kind):
        name   = self.consume(TokenType.IDENTIFIER, f'expect {kind} name')
        params = []

        self.consume(TokenType.LEFT_PAREN, f'expect \'(\' after {kind} name')

        if not self.check(TokenType.RIGHT_PAREN):
            params.append(self.consume(TokenType.IDENTIFIER, 'expect parameter name'))

            while self.match(TokenType.COMMA):
                params.append(self.consume(TokenType.IDENTIFIER, 'expect parameter name'))

        self.consume(TokenType.RIGHT_PAREN, 'expect \')\' after parameters')
        self.consume(TokenType.LEFT_BRACE, f'expect \'{{\' before {kind} body')

        return Function(name, params, self.block_statement())

    def class_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, 'expect class name')

        methods = []
        superclass = None

        if self.match(TokenType.LESS):
            self.consume(TokenType.IDENTIFIER, 'expect superclass name')
            superclass = Variable(self.previous())

        self.consume(TokenType.LEFT_BRACE, 'except \'{\' after class name')

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            # self.consume(TokenType.FN, 'expect \'fn\' before method name')
            methods.append(self.fn_declaration('method'))

        self.consume(TokenType.RIGHT_BRACE, 'expect \'}\' after class body')
        return Class(name, superclass, methods)

    def statement(self):
        if self.match(TokenType.IF): return self.if_statement()
        if self.match(TokenType.FOR): return self.for_statement()
        if self.match(TokenType.RETURN): return self.return_statement()
        if self.match(TokenType.WHILE): return self.while_statement()
        if self.match(TokenType.LEFT_BRACE): return self.block_statement()

        return self.expression_statement()

    def if_statement(self):
        branches = []
        else_branch = None

        self.consume(TokenType.LEFT_PAREN, 'expect \'(\' after if')
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, 'expect \')\' after if condition')
        branches.append((condition, self.statement()))

        while self.match(TokenType.ELSE) and self.match(TokenType.IF):
            self.consume(TokenType.LEFT_PAREN, 'expect \'(\' after if')
            condition = self.expression()
            self.consume(TokenType.RIGHT_PAREN, 'expect \')\' after if condition')
            branches.append((condition, self.statement()))

        if self.previous().type == TokenType.ELSE:
            else_branch = self.statement()

        return If(branches, else_branch)

    def block_statement(self):
        statements = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, 'expect \'}\' after')
        return Block(statements)

    def return_statement(self):
        value = None
        keyword = self.previous()

        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, 'expect \';\' after return value')
        return Return(keyword, value)

    def for_statement(self):
        self.consume(TokenType.LEFT_PAREN, 'expect \'(\' after for')

        if self.match(TokenType.SEMICOLON): init = None
        elif self.match(TokenType.LET):     init = self.var_declaration()
        else:                               init = self.expression_statement()

        condition = Literal(True) if self.check(TokenType.SEMICOLON) else self.expression()
        self.consume(TokenType.SEMICOLON, 'expect \';\' after loop condition')

        increment = None if self.check(TokenType.RIGHT_PAREN) else self.expression()
        self.consume(TokenType.RIGHT_PAREN, 'expect \')\' after for clauses')

        return Block([
            init,
            While(
                condition,
                Block([
                    self.statement(),
                    increment
                ])
            )
        ])

    def while_statement(self):
        self.consume(TokenType.LEFT_PAREN, 'expect \'(\' after while')
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, 'expect \')\' after while')

        return While(condition, self.statement())

    def expression_statement(self):
        value = self.expression()
        self.consume(TokenType.SEMICOLON, 'expect \';\' after expression')
        return Expression(value)

    def expression(self):
        return self.assignment()

    def assignment(self):
        expr = self.or_expr()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            rvalue = self.assignment()

            if isinstance(expr, Variable):
                return Assign(expr.name, rvalue)

            elif isinstance(expr, Get):
                return Set(expr.object, expr.name, rvalue)

            raise ParseError(equals, 'invalid assign target')

        return expr

    def or_expr(self):
        expr = self.and_expr()

        while self.match(TokenType.OR):
            expr = Logical(expr, self.previous(), self.and_expr())

        return expr

    def and_expr(self):
        expr = self.equality()

        while self.match(TokenType.AND):
            expr = Logical(expr, self.previous(), self.equality())

        return expr

    def equality(self):
        expr = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            expr = Binary(expr, self.previous(), self.comparison())

        return expr

    def comparison(self):
        expr = self.term()

        while self.match(
                TokenType.GREATER, TokenType.GREATER_EQUAL,
                TokenType.LESS, TokenType.LESS_EQUAL):
            expr = Binary(expr, self.previous(), self.term())

        return expr

    def term(self):
        expr = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            expr = Binary(expr, self.previous(), self.factor())

        return expr

    def factor(self):
        expr = self.unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            expr = Binary(expr, self.previous(), self.factor())

        return expr

    def unary(self):
        if self.match(TokenType.BANG, TokenType.MINUS):
            return Unary(self.previous(), self.unary())

        return self.call()

    def finish_call(self, callee):
        arguments = []

        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.expression())

            while self.match(TokenType.COMMA):
                arguments.append(self.expression())

        return Call(
            callee,
            self.consume(TokenType.RIGHT_PAREN, 'expect \')\' after arguments'), arguments)

    def call(self):
        expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, 'except property name after \'.\'')
                expr = Get(expr, name)
            else:
                break

        return expr

    def primary(self):
        if self.match(TokenType.NIL): return Literal(None)
        if self.match(TokenType.TRUE): return Literal(True)
        if self.match(TokenType.FALSE): return Literal(False)
        if self.match(TokenType.THIS): return This(self.previous())

        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous())

        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)

        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, 'expected \')\' after expression')
            return Grouping(expr)

        if self.match(TokenType.SUPER):
            keyword = self.previous()
            self.consume(TokenType.DOT, 'expect \'.\' after `super`')

            return Super(
                keyword,
                self.consume(TokenType.IDENTIFIER, 'expect superclass method name'))

        raise self.error('expect expression')
