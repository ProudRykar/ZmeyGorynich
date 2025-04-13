import re

def tokenize(code):
    """Токены для обработки парсером"""
    tokens = []
    token_specification = [
        ('число',   r'\d+(\.\d*)?'),                            # Числа
        ('ROOT', r'корешок из'),                                # Обработка корня
        ('GOYDA',   r'гойда'),                                  # Разделитель команд
        ('ОТКРЫТАЯФИГУРНАЯСКОБКА', r'ухожу я в пляс'),
        ('ЗАКРЫТАЯФИГУРНАЯСКОБКА', r'закончили пляски'),
        ('TYPE_ANNOTATION', r'быти'),                           # Ключевое слово для типизации
        ('DEF',   r'сотвори'), 
        ('RETURN_TYPE',   r'изречет'), 
        ('RETURN',   r'возверни'), 
        ('IMPORT', r'прочесть книгу'),                          # Ключевое слово для импорта
        ('DOT',     r'\.'),
        ('AS',      r'и осмыслить слова как'),
        ('ID', r'[A-Za-zА-Яа-яЀ-ӿꙀ-ꙿ\u16A0-\u16FF_]\w*'),       # Идентификаторы: кириллица + латиница + руны      
        ('OP', r'(\*\*|[+\-*/%]|[<>]=?|!=|==)'),                # Операторы: арифметические и сравнения
        ('ASSIGN',  r'='),                                      # Присваивание
        ('строченька',  r'"([^"\\]|\\.)*"'),                    # Строки
        ('NEWLINE', r'\n'),                                     # Новая строка
        ('COMMA',   r','),                                      # Запятая
        ('SKIP',    r'[ \t]+'),                                 # Пробелы и табуляции
        ('COMMENT', r'#.*?(?=\n|$)'),                           # Однострочные комментарии
        ('BRACKET', r'[\[\]]'),                                 # Квадратные скобки для массивов
        ('PARENTHESIS', r'[()]'),                               # Скобки
        ('MISMATCH', r'.'),                                     # Ошибка
    ]
    token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    
    line_num = 1
    line_start = 0
    pos = 0

    while pos < len(code):
        if code.startswith('Голос предков шепчет:', pos):
            comment_start_pos = pos
            pos += len('Голос предков шепчет:')
            comment_end_pos = code.find('Голос предков внезапно стих...', pos)
            if comment_end_pos == -1:
                raise SyntaxError(f"Оказия синтаксиса: Незакрытый комментарий (строка {line_num})")
            comment_content = code[pos:comment_end_pos]
            line_num += comment_content.count('\n')
            pos = comment_end_pos + len('Голос предков внезапно стих...')
            last_newline = code.rfind('\n', 0, pos)
            line_start = last_newline + 1 if last_newline != -1 else 0
            continue

        if code.startswith('#', pos):
            comment_end_pos = code.find('\n', pos)
            if comment_end_pos == -1:
                comment_end_pos = len(code)
            pos = comment_end_pos
            continue

        match = re.match(token_regex, code[pos:])
        if not match:
            raise SyntaxError(f"Оказия синтаксиса: Неизвестный символ на позиции {pos} (строка {line_num})")

        kind = match.lastgroup
        value = match.group(kind)
        start_pos = pos
        column = start_pos - line_start + 1

        if kind == 'NEWLINE':
            line_num += 1
            line_start = start_pos + 1

        elif kind in ('SKIP', 'COMMENT'):
            pos += len(value)
            continue

        else:
            tokens.append((kind, value, line_num, column))

        pos += len(value)

    return tokens