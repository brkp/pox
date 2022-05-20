# coding: utf-8

SYNTAX_ERROR_TEMPLATE = '''\
  {line} | {line_text}
SyntaxError: {message}'''

def build_syntax_error(scanner, message, line=None):
    line = line if line else scanner.line

    return SYNTAX_ERROR_TEMPLATE.format(
        line=line,
        line_text=scanner.source.split('\n')[line - 1],
        message=message)

def build_parse_error(parser, message):
    return f'{parser.peek()}: {message}'

# TODO: implement this properly
def decode_escapes(s):
    for i, c in enumerate('abtnvfr'):
        s = s.replace(f'\\{c}', chr(7 + i))

    return s
