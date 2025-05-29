import pytest
import os
from lexer import tokenize
from parser import parse
from evaluator import evaluate, Context

@pytest.fixture
def context():
    return Context()

def test_evaluate_assignment(context):
    code = 'x быти цело = 42 гойда'
    tokens = tokenize(code)
    ast = parse(tokens, code)
    evaluate(ast, context)
    assert context.variables['x'] == 42
    assert context.type_hints['x'] == 'число:int'

def test_evaluate_print(context, capsys):
    code = 'молвить(42) гойда'
    tokens = tokenize(code)
    ast = parse(tokens, code)
    evaluate(ast, context)
    captured = capsys.readouterr()
    assert captured.out == '42\n'

def test_evaluate_if(context, capsys):
    code = '''
    x быти цело = 5 гойда
    аще x > 0 то
        ухожу я в пляс
            молвить("положительное") гойда
        закончили пляски
    '''
    tokens = tokenize(code)
    ast = parse(tokens, code)
    evaluate(ast, context)
    captured = capsys.readouterr()
    assert captured.out == 'положительное\n'

def test_evaluate_while(context):
    code = '''
    x быти цело = 0 гойда
    покуда x < 3
        ухожу я в пляс
            x = x + 1 гойда
        закончили пляски
    '''
    tokens = tokenize(code)
    ast = parse(tokens, code)
    evaluate(ast, context)
    assert context.variables['x'] == 3

def test_evaluate_function_call(context):
    code = '''
    сотвори удвоить(x быти цело) изречет цело
        ухожу я в пляс
            возверни x * 2
        закончили пляски
    y быти цело = удвоить(5) гойда
    '''
    tokens = tokenize(code)
    ast = parse(tokens, code)
    evaluate(ast, context)
    assert context.variables['y'] == 10

def test_evaluate_type_error(context):
    code = 'х быти строченька = 42 гойда'
    tokens = tokenize(code)
    ast = parse(tokens, code)
    with pytest.raises(TypeError, match="Значение должно быть строченькой"):
        evaluate(ast, context)