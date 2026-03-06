from node import Node
from colored_text import Color

TYPE_MAP = {
    'цело': 'число:int',
    'плывун': 'число:float',
    'строченька': 'строченька',
    'двосуть': 'двосуть',
    'плывун малый точный': 'decimal:30',
    'плывун великий': 'decimal:50',
    'плывун звездный': 'decimal:100',
    'список цело': 'list:число:int',
    'список плывун': 'list:число:float',
    'список строченька': 'list:строченька',
    'список двосуть': 'list:двосуть'
}

def get_line_at(code, line_num):
    """Получить строку кода по номеру строки."""
    lines = code.split('\n')
    return lines[line_num - 1] if 1 <= line_num <= len(lines) else ""


def get_context(code, line_num, col):
    lines = code.split('\n')
    context = []
    if line_num > 1:
        context.append(f"{Color.CYAN.value} {line_num-1:3d} | {lines[line_num-2]}{Color.RESET_ALL.value}")
    context.append(f"{Color.RED.value} {line_num:3d} |  {lines[line_num-1]}{Color.RESET_ALL.value}")
    context.append(f"{Color.RED.value}     | {' ' * (col-1)}{Color.RED.value}→{Color.RESET_ALL.value}")
    return "\n".join(context)


def parse(tokens, code):
    i = 0

    def cur():
        return tokens[i] if i < len(tokens) else (None, None, None, None)

    def advance():
        nonlocal i
        i += 1

    def accept(kind, value=None):
        k, v, _, _ = cur()
        if k == kind and (value is None or v == value):
            advance()
            return True
        return False

    def expect(kind, value=None, msg=None, line=None, col=None):
        k, v, ln, cl = cur()
        if k != kind or (value is not None and v != value):
            ln = ln or line or 0
            cl = cl or col or 0
            ctx = get_context(code, ln, cl)
            base = f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} "
            raise SyntaxError(base + (msg or f"Ожидался {kind}('{value}')") + f"\n{ctx}")
        advance()
        return v

    def error_ctx_from(token_idx=None):
        if token_idx is None:
            k, v, ln, cl = cur()
        else:
            k, v, ln, cl = tokens[token_idx] if token_idx < len(tokens) else (None, None, 1, 1)
        return get_context(code, ln or 1, cl or 1)

    def parse_primary():
        """Нижний уровень: числа, строки, ID (+вызовы/индексация), скобки, массив, корень"""
        nonlocal i
        k, v, ln, cl = cur()
        if k is None:
            return None

        if k == 'строченька':
            advance()
            return Node('строченька', value=v, line=ln, col=cl)

        if k == 'число':
            advance()
            return Node('число', value=v, line=ln, col=cl)

        if k == 'ROOT':
            advance()
            expr = parse_expression()
            if not expr:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось выражение после 'корень из'\n{error_ctx_from(i)}")
            return Node('RootOp', children=[expr])

        if k == 'BRACKET' and v == '[':
            # массив
            advance()
            elems = []
            while not (cur()[0] == 'BRACKET' and cur()[1] == ']'):
                elem = parse_expression()
                if elem:
                    elems.append(elem)
                if cur()[0] == 'COMMA':
                    advance()
                elif cur()[0] == 'BRACKET' and cur()[1] == ']':
                    break
                else:
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалась запятая или ']' в массиве\n{error_ctx_from(i)}")
            expect('BRACKET', ']', msg="Незакрытый массив")
            return Node('Array', children=elems)

        if k == 'PARENTHESIS' and v == '(':
            advance()
            expr = parse_expression()
            expect('PARENTHESIS', ')', msg="Незакрытая скобка")
            return expr

        if k == 'ID':
            # собрать многосоставный идентификатор через DOT
            id_parts = [v]
            ln_id, cl_id = ln, cl
            advance()
            while cur()[0] == 'DOT':
                advance()
                if cur()[0] != 'ID':
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался идентификатор после '.'\n{get_context(code, ln_id, cl_id)}")
                id_parts.append(cur()[1]); advance()
            id_value = '.'.join(id_parts)
            node = Node('ID', value=id_value, line=ln_id, col=cl_id)

            if cur()[0] == 'PARENTHESIS' and cur()[1] == '(':
                advance()
                args = parse_comma_separated('PARENTHESIS', ')', allow_empty=False, element_parser=parse_expression,
                                             error_msg="Ожидалось выражение в аргументах функции")
                return Node('Call', value=id_value, children=args, line=ln_id, col=cl_id)

            if id_value == 'созвать_дружину' and cur()[0] == 'PARENTHESIS' and cur()[1] == '(':
                return parse_array_create_specific(ln_id, cl_id)

            if cur()[0] == 'BRACKET' and cur()[1] == '[':
                advance()
                idx = parse_expression()
                if not idx:
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался индекс после '['\n{get_context(code, ln_id, cl_id)}")
                expect('BRACKET', ']', msg="Ожидалась ']' после индекса", line=ln_id, col=cl_id)
                return Node('ArrayAccess', children=[node, idx])
            return node

        return None

    def parse_comma_separated(close_kind, close_value, allow_empty, element_parser, error_msg):
        """Парсинг списков элементов (аргументы, элементы массива). Возвращает список."""
        elems = []
        if cur()[0] == close_kind and cur()[1] == close_value:
            advance()
            return elems
        while True:
            elem = element_parser()
            if not elem:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} {error_msg}\n{error_ctx_from(i)}")
            elems.append(elem)
            if cur()[0] == 'COMMA':
                advance()
                continue
            if cur()[0] == close_kind and cur()[1] == close_value:
                advance()
                break
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалась запятая или '{close_value}'\n{error_ctx_from(i)}")
        return elems

    def parse_array_create_specific(line, col):
        """Парсинг создания массива - созвать_дружину"""

        if cur()[0] == 'PARENTHESIS' and cur()[1] == '(':
            advance()
        size_expr = parse_expression()
        if not size_expr:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался размер массива в 'созвать_дружину'\n{get_context(code, line, col)}")
        expect('COMMA', msg="Ожидалась запятая после размера в 'созвать_дружину'", line=line, col=col)
        value_expr = parse_expression()
        if not value_expr:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось значение для заполнения массива в 'созвать_дружину'\n{get_context(code, line, col)}")
        expect('PARENTHESIS', ')', msg="Ожидалась ')' после аргументов в 'созвать_дружину'", line=line, col=col)
        return Node('ArrayCreate', children=[size_expr, value_expr])

    def parse_left_assoc(subparser, ops):
        left = subparser()
        if not left:
            return None
        while cur()[0] == 'OP' and cur()[1] in ops:
            op = cur()[1]
            advance()
            right = subparser()
            if not right:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось выражение после '{op}'\n{error_ctx_from(i-1)}")
            left = Node('BinaryOp', op=op, children=[left, right])
        return left

    def parse_expression():
      """Выражение с приоритетами и сравнениями"""

      def parse_comparison():
          left = parse_additive()
          if not left:
              return None

          if cur()[0] == 'OP' and cur()[1] in (
              '<', '>', '<=', '>=', '==', '!=',
              'равно', 'не равно',
              'превосходит', 'уступает',
              'ровно либо превосходит',
              'ровно либо уступает'
          ):
              op = cur()[1]
              advance()
              right = parse_additive()
              if not right:
                  raise SyntaxError(
                      f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} "
                      f"Ожидалось выражение после '{op}'\n{error_ctx_from(i-1)}"
                  )
              return Node('BinaryOp', op=op, children=[left, right])

          return left

      def parse_additive():
          return parse_left_assoc(
              parse_multiplicative,
              ('+', '-', 'прибави', 'отними')
          )

      def parse_multiplicative():
          return parse_left_assoc(
              parse_power,
              ('*', '/', '%', 'умножи на', 'раздели на', 'остаток от')
          )

      def parse_power():
          left = parse_primary()
          if not left:
              return None

          if cur()[0] == 'OP' and cur()[1] in ('**', 'возвысить в'):
              op = cur()[1]
              advance()
              right = parse_power()
              if not right:
                  raise SyntaxError(
                      f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} "
                      f"Ожидалось выражение после '{op}'\n{error_ctx_from(i-1)}"
                  )
              return Node('BinaryOp', op=op, children=[left, right])

          return left

      return parse_comparison()
    
    def parse_expression_statement():
      expr = parse_expression()
      if expr and cur()[0] == 'GOYDA':
          advance()
          return Node('ExpressionStatement', children=[expr])
      return None

    def parse_assignment():
        nonlocal i
        start = i
        if cur()[0] != 'ID':
            return None
        var_name = cur()[1]; line, col = cur()[2], cur()[3]
        var_node = Node('ID', value=var_name, line=line, col=col)
        advance()

        # типизация
        type_hint = None
        if cur()[0] == 'TYPE_ANNOTATION':
            advance()
            if cur()[0] != 'ID':
                raise SyntaxError(f"Ожидался тип после 'быти' (строка {line}, столбец {col})")
            # собрать составной тип
            parts = []
            while cur()[0] == 'ID' and cur()[1] not in ('=', 'гойда'):
                parts.append(cur()[1]); advance()
            type_name = ' '.join(parts)
            type_hint = TYPE_MAP.get(type_name)
            if type_hint is None:
                raise SyntaxError(f"Неизвестный тип '{type_name}' (строка {line}, столбец {col})")

        # ID[expr] = expr
        if cur()[0] == 'BRACKET' and cur()[1] == '[':
            advance()
            idx = parse_expression()
            if not idx:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался индекс после '['\n{get_context(code, line, col)}")
            expect('BRACKET', ']', msg="Ожидалась ']' после индекса", line=line, col=col)
            if cur()[0] == 'ASSIGN':
                advance()
                expr = parse_expression()
                if cur()[0] == 'GOYDA':
                    advance()
                    return Node('ArrayAssignment', children=[var_node, idx, expr], type_hint=type_hint, line=line, col=col)
                raise SyntaxError(f"Ожидалась 'гойда' после присваивания\n{get_context(code, line, col)}")
            i = start
            return None

        # ID = expr
        if cur()[0] == 'ASSIGN':
            advance()
            expr = parse_expression()
            if expr and getattr(expr, 'type', None) == 'число' and type_hint:
                expr.type_hint = type_hint
            if cur()[0] == 'GOYDA':
                advance()
                return Node('Assignment', children=[var_node, expr], type_hint=type_hint, line=line, col=col)
            raise SyntaxError(f"Ожидалась 'гойда' после присваивания\n{get_context(code, line, col)}")

        i = start
        return None

    def parse_print():
        """Парсинг функции молвить (print) и молвить(... и эхом затихнуть)"""
        nonlocal i
        if cur()[0] != 'ID' or cur()[1] != 'молвить':
            return None
        line, col = cur()[2], cur()[3]; advance()

        expr_nodes = []
        if cur()[0] == 'PARENTHESIS' and cur()[1] == '(':
            advance()
            expr_nodes = parse_comma_separated('PARENTHESIS', ')', allow_empty=False, element_parser=parse_expression,
                                              error_msg="Ожидалось выражение в 'молвить'")
        else:
            # однотомный вариант: молвить идентификатор
            if cur()[0] == "строченька":
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Строки после 'молвить' должны заключаться в ()\n{error_ctx_from(i)}")
            if cur()[0] != 'ID':
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалась переменная после 'молвить'\n{error_ctx_from(i)}")
            expr_nodes = [Node('ID', value=cur()[1], line=cur()[2], col=cur()[3])]
            advance()

        # опция "и эхом затихнуть"
        is_silent = (cur()[0] == 'ID' and cur()[1] == 'и' and
                     (i+2) < len(tokens) and tokens[i+1][0] == 'ID' and tokens[i+1][1] == 'эхом' and
                     tokens[i+2][0] == 'ID' and tokens[i+2][1] == 'затихнуть')
        if is_silent:
            advance(); advance(); advance()

        expect('GOYDA', msg="Ожидалась 'гойда' после 'молвить'", line=line, col=col)
        return Node('PrintWithSilence' if is_silent else 'Print', children=expr_nodes, line=line, col=col)

    def parse_input():
        """Парсинг функции внемли (input) с опциональным сообщением в скобках"""
        nonlocal i
        if cur()[0] != 'ID' or cur()[1] != 'внемли':
            return None
        line, col = cur()[2], cur()[3]; advance()
        expect('PARENTHESIS', '(', msg="Ожидалась '(' после 'внемли'", line=line, col=col)

        prompt_node = None
        if cur()[0] == 'строченька':
            prompt_node = Node('строченька', value=cur()[1].strip('"'), line=cur()[2], col=cur()[3]); advance()
            expect('COMMA', msg="Ожидалась запятая ',' после строки", line=line, col=col)

        if cur()[0] != 'ID':
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалась переменная\n{error_ctx_from(i)}")
        var_node = Node('ID', value=cur()[1], line=cur()[2], col=cur()[3]); advance()
        expect('PARENTHESIS', ')', msg="Ожидалась ')' после переменной", line=line, col=col)
        expect('GOYDA', msg="Ожидалась 'гойда' после 'внемли(...)'", line=line, col=col)

        children = [var_node] if not prompt_node else [prompt_node, var_node]
        return Node('Input', children=children, line=line, col=col)

    def parse_while():
        """Парсинг цикла покуда (while)"""
        nonlocal i
        if cur()[0] != 'ID' or cur()[1] != 'покуда':
            return None
        line, col = cur()[2], cur()[3]; advance()
        condition = parse_expression()
        if not condition:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось условие после 'покуда'\n{get_context(code, line, col)}")
        expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после условия в 'покуда'", line=line, col=col)

        body = []
        while cur()[0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
            stmt = parse_any_statement_inside_loop()
            if stmt:
                body.append(stmt)
            else:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Неожиданный токен '{cur()[1]}' в теле 'покуда'\n{error_ctx_from(i)}")
        expect('ЗАКРЫТАЯФИГУРНАЯСКОБКА')
        return Node('While', children=[condition, Node('Block', children=body)])

    def parse_array_create():
        """Парсинг создания массива - созвать_дружину"""
        nonlocal i
        if cur()[0] != 'ID' or cur()[1] != 'созвать_дружину':
            return None
        line, col = cur()[2], cur()[3]; advance()
        expect('PARENTHESIS', '(', msg="Ожидалось '(' после 'созвать_дружину'", line=line, col=col)
        size_expr = parse_expression()
        if not size_expr:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался размер массива в 'созвать_дружину'\n{get_context(code, line, col)}")
        expect('COMMA', msg="Ожидалась запятая после размера в 'созвать_дружину'", line=line, col=col)
        value_expr = parse_expression()
        if not value_expr:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось значение для заполнения массива в 'созвать_дружину'\n{get_context(code, line, col)}")
        expect('PARENTHESIS', ')', msg="Ожидалась ')' после аргументов в 'созвать_дружину'", line=line, col=col)
        return Node('ArrayCreate', children=[size_expr, value_expr])

    def parse_if():
        """Парсинг условий аще - аще ли - ино (if-elif-else)"""
        nonlocal i
        if cur()[0] != 'ID' or cur()[1] != 'аще':
            return None
        line, col = cur()[2], cur()[3]; advance()
        condition = parse_expression()
        if not condition:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось условие после 'аще'\n{get_context(code, line, col)}")
        expect('ID', 'то', msg="Ожидалось 'то' после условия", line=line, col=col)
        expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после 'то'", line=line, col=col)

        def parse_block_until_close(allowed_stmt_parsers):
            body = []
            while cur()[0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                stmt = None
                for p in allowed_stmt_parsers:
                    stmt = p()
                    if stmt:
                        body.append(stmt)
                        break
                if not stmt:
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Неожиданный токен '{cur()[1]}' в теле\n{error_ctx_from(i)}")
            expect('ЗАКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'закончили пляски' после тела", line=line, col=col)
            return body

        if_body = parse_block_until_close([parse_assignment, parse_print, parse_input, parse_while, parse_if, parse_return, parse_fixed_loop])
        # elif branches
        elif_branches = []
        while cur()[0] == 'ID' and cur()[1] == 'аще':
            advance()
            expect('ID', 'ли', msg="Ожидалось 'ли' после 'аще' для 'аще ли'", line=line, col=col)
            elif_cond = parse_expression()
            expect('ID', 'то', msg="Ожидалось 'то' после условия в 'аще ли'", line=line, col=col)
            expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после 'то' в 'аще ли'", line=line, col=col)
            elif_body = parse_block_until_close([parse_assignment, parse_print, parse_input, parse_while, parse_if, parse_return])
            elif_branches.append((elif_cond, Node('Block', children=elif_body)))

        else_body = []
        if cur()[0] == 'ID' and cur()[1] == 'ино':
            advance()
            expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после 'ино'", line=line, col=col)
            else_body = parse_block_until_close([parse_assignment, parse_print, parse_input, parse_while, parse_if, parse_return, parse_fixed_loop])

        return Node('If', children=[
            condition,
            Node('Block', children=if_body),
            Node('ElifBlocks', children=[Node('Elif', children=[cond, block]) for cond, block in elif_branches]),
            Node('Block', children=else_body)
        ])

    def parse_function():
        """Парсинг конструкции функции (def)"""
        nonlocal i
        if cur()[0] != 'DEF':
            return None
        line, col = cur()[2], cur()[3]; advance()
        if cur()[0] != 'ID':
            raise SyntaxError(f"Ожидалось имя функции после 'сотвори'\n{get_context(code, line, col)}")
        func_name = cur()[1]; advance()
        expect('PARENTHESIS', '(', msg="Ожидалось '(' после имени функции", line=line, col=col)

        args = []
        if not (cur()[0] == 'PARENTHESIS' and cur()[1] == ')'):
            while True:
                if cur()[0] != 'ID':
                    raise SyntaxError(f"Ожидалось имя аргумента (получен {cur()[0]}: '{cur()[1]}')\n{get_context(code, line, col)}")
                arg_name = cur()[1]; arg_line, arg_col = cur()[2], cur()[3]; advance()
                arg_type = None
                if cur()[0] == 'TYPE_ANNOTATION' and cur()[1] == 'быти':
                    advance()
                    if cur()[0] != 'ID':
                        raise SyntaxError(f"Ожидался тип после 'быти'\n{get_context(code, arg_line, arg_col)}")
                    parts = []
                    while cur()[0] == 'ID' and cur()[1] not in ('=', 'гойда', ')', ','):
                        parts.append(cur()[1]); advance()
                    type_name = ' '.join(parts)
                    arg_type = TYPE_MAP.get(type_name)
                    if arg_type is None:
                        raise SyntaxError(f"Неизвестный тип '{type_name}'\n{get_context(code, arg_line, arg_col)}")
                args.append(Node('Arg', value=arg_name, type_hint=arg_type))
                if cur()[0] == 'COMMA':
                    advance()
                    continue
                break
        expect('PARENTHESIS', ')', msg="Ожидалось ')' после аргументов", line=line, col=col)
        expect('RETURN_TYPE', msg="Ожидалось 'изречет' после аргументов", line=line, col=col)
        # сбор типа возврата
        if cur()[0] != 'ID':
            raise SyntaxError(f"Ожидался тип возврата после 'изречет'\n{get_context(code, line, col)}")
        parts = []
        while cur()[0] == 'ID' and cur()[1] not in ('гойда', 'ухожу я в пляс'):
            parts.append(cur()[1]); advance()
        return_type = ' '.join(parts)
        if return_type not in TYPE_MAP:
            raise SyntaxError(f"Неизвестный тип возврата '{return_type}'\n{get_context(code, line, col)}")
        return_type = TYPE_MAP[return_type]
        expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после типа возврата", line=line, col=col)

        body = []
        while cur()[0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
            stmt = parse_any_statement_inside_function()
            if stmt:
                body.append(stmt)
            else:
                raise SyntaxError(f"Неожиданный токен '{cur()[1]}' в теле функции\n{error_ctx_from(i)}")
        expect('ЗАКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'закончили пляски' после тела функции", line=line, col=col)
        return Node('Function', value=func_name, children=[Node('Args', children=args), Node('Block', children=body)], type_hint=return_type)

    def parse_return():
        """Парсинг return"""
        nonlocal i
        if cur()[0] != 'RETURN':
            return None
        line, col = cur()[2], cur()[3]; advance()
        expr = parse_expression()
        if not expr:
            raise SyntaxError(f"Ожидалось выражение после 'возверни'\n{get_context(code, line, col)}")
        if cur()[0] == 'GOYDA':
            advance()
        return Node('Return', children=[expr])

    def parse_call():
        """Парсинг вызова функции"""
        nonlocal i
        if cur()[0] != 'ID':
            return None
        func_name = cur()[1]; line, col = cur()[2], cur()[3]; advance()
        if not (cur()[0] == 'PARENTHESIS' and cur()[1] == '('):
            i -= 1
            return None
        advance()
        args = parse_comma_separated('PARENTHESIS', ')', allow_empty=True, element_parser=parse_expression,
                                     error_msg="Ожидалась запятая или ')' в аргументах функции")
        if cur()[0] != 'GOYDA':
            raise SyntaxError(f"Ожидалась 'гойда' после вызова функции\n{get_context(code, line, col)}")
        advance()
        return Node('Call', value=func_name, children=args, line=line, col=col)

    def parse_fixed_loop():
        """Парсинг фиксированных циклов Дважды, Трижды, Четырежды"""
        nonlocal i
        loop_types = {
            'дважды': 2, 'трижды': 3, 'четырежды': 4, 'пятьжды': 5,
            'шестьжды': 6, 'семьжды': 7, 'осьмьжды': 8, 'девятьжды': 9,
            'десятьжды': 10, 'стожды': 100,
        }
        if cur()[0] == 'ID' and cur()[1].lower() in loop_types:
            loop_name = cur()[1].lower(); iterations = loop_types[loop_name]
            line, col = cur()[2], cur()[3]; advance()
            body = []
            if cur()[0] == 'ОТКРЫТАЯФИГУРНАЯСКОБКА':
                advance()
                while cur()[0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                    stmt = (parse_assignment() or parse_print() or parse_input() or parse_while()
                            or parse_if() or parse_fixed_loop() or parse_return() or parse_call())
                    if stmt:
                        body.append(stmt)
                    else:
                        raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Неожиданный токен '{cur()[1]}' в теле '{loop_name}'\n{error_ctx_from(i)}")
                expect('ЗАКРЫТАЯФИГУРНАЯСКОБКА', msg=f"Ожидалось 'закончили пляски' после тела '{loop_name}'", line=line, col=col)
            else:
                stmt = (parse_assignment() or parse_print() or parse_input() or parse_while()
                        or parse_if() or parse_fixed_loop() or parse_return() or parse_call())
                if not stmt:
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался оператор после '{loop_name}'\n{get_context(code, line, col)}")
                body.append(stmt)
            return Node('FixedLoop', value=iterations, children=[Node('Block', children=body)])
        return None

    def parse_import():
        """Парсинг конструкции импорта (взять из 'файл.zg' [как псевдоним] или прочесть книгу 'файл.zg' [и осмыслить текст как псевдоним])"""
        nonlocal i
        if cur()[0] != 'IMPORT':
            return None
        line, col = cur()[2], cur()[3]; advance()
        if cur()[0] != 'строченька':
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось имя файла в кавычках после 'взять из' или 'прочесть книгу'\n{get_context(code, line, col)}")
        filename = cur()[1].strip('"'); advance()
        alias = None
        if cur()[0] in ('AS', 'OLD_AS'):
            advance()
            if cur()[0] != 'ID':
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался идентификатор после 'как' или 'и осмыслить текст как'\n{get_context(code, line, col)}")
            alias = cur()[1]; advance()
        expect('GOYDA', msg="Ожидалась 'гойда' после конструкции импорта", line=line, col=col)
        if not alias:
            alias = filename.rsplit('.', 1)[0]
        return Node('Import', value=filename, alias=alias, line=line, col=col)

    # вспомогательные для использования внутри блоков (чтобы не дублировать список парсеров)
    def parse_any_statement_inside_loop():
        return (parse_assignment() or parse_print() or parse_input() or parse_while() or parse_if()
                or parse_return() or parse_fixed_loop())

    def parse_any_statement_inside_function():
        return (parse_assignment() or parse_print() or parse_input() or parse_while() or parse_if()
                or parse_function() or parse_return() or parse_fixed_loop())

    # --- основной проход по токенам
    ast = []
    while i < len(tokens):
        if cur()[0] == 'NEWLINE':
            advance(); continue
        parsers = (parse_if, parse_while, parse_input, parse_print, parse_assignment,
                   parse_array_create, parse_function, parse_call, parse_fixed_loop, parse_import, parse_expression_statement)
        for p in parsers:
            stmt = p()
            if stmt:
                ast.append(stmt)
                break
        else:
            # ни один парсер не сработал
            k, v, ln, cl = cur()
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Неожиданный токен '{v}'\n{get_context(code, ln, cl)}")

    return ast