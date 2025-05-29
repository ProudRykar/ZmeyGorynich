import pytest
from lexer import tokenize
from parser import parse, Node, get_context

def test_parse_assignment():
    code = 'x быти цело = 42 гойда'
    tokens = tokenize(code)
    ast = parse(tokens, code)
    assert len(ast) == 1
    node = ast[0]
    assert node.type == 'Assignment'
    assert node.children[0].type == 'ID'
    assert node.children[0].value == 'x'
    assert node.children[1].type == 'число'
    assert node.children[1].value == '42'
    assert node.type_hint == 'число:int'

def test_parse_function_call():
    code = 'молвить(42) гойда'
    tokens = tokenize(code)
    ast = parse(tokens, code)
    assert len(ast) == 1
    node = ast[0]
    assert node.type == 'Print'
    assert node.children[0].type == 'число'
    assert node.children[0].value == '42'

def test_parse_if_statement():
    code = '''
    аще x > 0 то
        ухожу я в пляс
            молвить("положительное") гойда
        закончили пляски
    '''
    tokens = tokenize(code)
    ast = parse(tokens, code)
    assert len(ast) == 1
    node = ast[0]
    assert node.type == 'If'
    assert node.children[0].type == 'Condition'
    assert node.children[0].op == '>'
    assert node.children[1].type == 'Block'

def test_parse_while_loop():
    code = '''
    покуда x < 10
        ухожу я в пляс
            x = x + 1 гойда
        закончили пляски
    '''
    tokens = tokenize(code)
    ast = parse(tokens, code)
    assert len(ast) == 1
    node = ast[0]
    assert node.type == 'While'
    assert node.children[0].type == 'Condition'
    assert node.children[0].op == '<'
    assert node.children[1].type == 'Block'

def test_parse_function_definition():
    code = '''
    сотвори добавить(x быти цело, y быти цело) изречет цело
        ухожу я в пляс
            возверни x + y
        закончили пляски
    '''
    tokens = tokenize(code)
    ast = parse(tokens, code)
    assert len(ast) == 1
    node = ast[0]
    assert node.type == 'Function'
    assert node.value == 'добавить'
    assert node.type_hint == 'число:int'
    assert len(node.children[0].children) == 2
    assert node.children[0].children[0].type_hint == 'число:int'

def test_parse_invalid_syntax():
    code = 'x = 42'  # Отсутствует 'гойда'
    tokens = tokenize(code)
    with pytest.raises(SyntaxError, match="Ожидалась 'гойда'"):
        parse(tokens, code)