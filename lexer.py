#vsce package
import re

def tokenize(code):
    tokens = []
    token_specification = [
        ('число',   r'\d+(\.\d*)?'),      # Числа
        ('ROOT', r'корешок из'),             # Обработка корня
        ('GOYDA',   r'гойда'),            # Разделитель команд
        ('ОТКРЫТАЯФИГУРНАЯСКОБКА', r'ухожу я в пляс'),
        ('ЗАКРЫТАЯФИГУРНАЯСКОБКА', r'закончили пляски'),
        ('ID',      r'[А-Яа-я_]\w*'),     # Идентификаторы
        ('ASSIGN',  r'='),                # Присваивание
        ('OP', r'(\*\*|[+\-*/%]|[<>]=?|!=|=)'),  # Операторы: арифметические и сравнения
        ('строченька',  r'"([^"\\]|\\.)*"'),  # Строки
        ('NEWLINE', r'\n'),               # Новая строка
        ('COMMA',   r','),                # Запятая
        ('SKIP',    r'[ \t]+'),           # Пробелы и табуляции
        ('COMMENT', r'#.*?(?=\n|$)'),     # Комментарии до конца строки
        ('BRACKET', r'[\[\]]'),           # Квадратные скобки для массивов
        ('PARENTHESIS', r'[()]'),         # Скобки
        ('MISMATCH', r'.'),               # Ошибка
    ]
    token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    
    line_num = 1  # Номер строки
    line_start = 0  # Начальная позиция текущей строки в тексте
    
    for match in re.finditer(token_regex, code):
        kind = match.lastgroup
        value = match.group(kind)
        start_pos = match.start()  # Позиция начала токена в тексте
        column = start_pos - line_start + 1  # Позиция в строке (считаем с 1)
        
        if kind == 'NEWLINE':
            line_num += 1
            line_start = start_pos + 1  # Обновляем начало следующей строки
        elif kind not in ('SKIP', 'COMMENT'):
            tokens.append((kind, value, line_num, column))
    
    return tokens