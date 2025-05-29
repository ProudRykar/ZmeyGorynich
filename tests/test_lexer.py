import pytest
from lexer import tokenize

def test_tokenize_basic():
    code = 'x = 42 гойда'
    tokens = tokenize(code)
    expected = [
        ('ID', 'x', 1, 1),
        ('ASSIGN', '=', 1, 3),
        ('число', '42', 1, 5),
        ('GOYDA', 'гойда', 1, 8)
    ]
    assert tokens == expected

def test_tokenize_string():
    code = '"привет" гойда'
    tokens = tokenize(code)
    expected = [
        ('строченька', '"привет"', 1, 1),
        ('GOYDA', 'гойда', 1, 10)
    ]
    assert tokens == expected

def test_tokenize_boolean():
    code = 'x = истина гойда'
    tokens = tokenize(code)
    expected = [
        ('ID', 'x', 1, 1),
        ('ASSIGN', '=', 1, 3),
        ('ID', 'истина', 1, 5),
        ('GOYDA', 'гойда', 1, 12)
    ]
    assert tokens == expected

def test_tokenize_function_call():
    code = 'молвить(x) гойда'
    tokens = tokenize(code)
    expected = [
        ('ID', 'молвить', 1, 1),
        ('PARENTHESIS', '(', 1, 8),
        ('ID', 'x', 1, 9),
        ('PARENTHESIS', ')', 1, 10),
        ('GOYDA', 'гойда', 1, 12)
    ]
    assert tokens == expected

def test_tokenize_comments():
    code = '# Это комментарий\nx = 42 гойда'
    tokens = tokenize(code)
    expected = [
        ('ID', 'x', 2, 1),
        ('ASSIGN', '=', 2, 3),
        ('число', '42', 2, 5),
        ('GOYDA', 'гойда', 2, 8)
    ]
    assert tokens == expected

def test_tokenize_multi_line_comment():
    code = 'Голос предков шепчет: текст\nГолос предков внезапно стих...\nx = 42 гойда'
    tokens = tokenize(code)
    expected = [
        ('ID', 'x', 3, 1),
        ('ASSIGN', '=', 3, 3),
        ('число', '42', 3, 5),
        ('GOYDA', 'гойда', 3, 8)
    ]
    assert tokens == expected
