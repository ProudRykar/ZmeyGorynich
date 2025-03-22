import re

def tokenize(code):
    tokens = []
    token_specification = [
        ('число',   r'\d+(\.\d*)?'),                            # Числа
        ('ROOT', r'корешок из'),                                # Обработка корня
        ('GOYDA',   r'гойда'),                                  # Разделитель команд
        ('ОТКРЫТАЯФИГУРНАЯСКОБКА', r'ухожу я в пляс'),
        ('ЗАКРЫТАЯФИГУРНАЯСКОБКА', r'закончили пляски'),
        ('TYPE_ANNOTATION', r'быти'),                           # Ключевое слово для типизации
        ('ID',      r'[А-Яа-яЀ-ӿꙀ-ꙿ_]\w*'),                     # Идентификаторы
        ('OP', r'(\*\*|[+\-*/%]|[<>]=?|!=|==)'),                # Операторы: арифметические и сравнения
        ('ASSIGN',  r'='),                                      # Присваивание
        ('строченька',  r'"([^"\\]|\\.)*"'),                    # Строки
        ('NEWLINE', r'\n'),                                     # Новая строка
        ('COMMA',   r','),                                      # Запятая
        ('SKIP',    r'[ \t]+'),                                 # Пробелы и табуляции
        ('COMMENT', r'#.*?(?=\n|$)'),                           # Комментарии до конца строки
        ('BRACKET', r'[\[\]]'),                                 # Квадратные скобки для массивов
        ('PARENTHESIS', r'[()]'),                               # Скобки
        ('MISMATCH', r'.'),                                     # Ошибка
    ]
    token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    
    line_num = 1
    line_start = 0
    
    for match in re.finditer(token_regex, code):
        kind = match.lastgroup
        value = match.group(kind)
        start_pos = match.start()
        column = start_pos - line_start + 1
        
        if kind == 'NEWLINE':
            line_num += 1
            line_start = start_pos + 1
        elif kind not in ('SKIP', 'COMMENT'):
            tokens.append((kind, value, line_num, column))
    
    return tokens