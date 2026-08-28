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
    if line_num is None or line_num < 1 or line_num > len(lines):
        if not lines:
            return ""
        line_num = max(1, min(line_num or 1, len(lines)))
    context = [f"строка {line_num}:"]
    if line_num > 1:
        context.append(f"{Color.CYAN.value} {line_num-1:3d} | {lines[line_num-2]}{Color.RESET_ALL.value}")
    context.append(f"{Color.RED.value} {line_num:3d} |  {lines[line_num-1]}{Color.RESET_ALL.value}")
    context.append(f"{Color.RED.value}     | {' ' * (col-1)}{Color.RED.value}→{Color.RESET_ALL.value}")
    return "\n".join(context)


class Parser:
    def __init__(self, tokens, code):
        self.tokens = tokens
        self.code = code
        self.i = 0
        self.errors = []

    # --- низкоуровневые помощники ---
    def cur(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else (None, None, None, None)

    def advance(self):
        self.i += 1

    def accept(self, kind, value=None):
        k, v, _, _ = self.cur()
        if k == kind and (value is None or v == value):
            self.advance()
            return True
        return False

    def expect(self, kind, value=None, msg=None, line=None, col=None):
        k, v, ln, cl = self.cur()
        if k != kind or (value is not None and v != value):
            ln = ln or line or 0
            cl = cl or col or 0
            ctx = get_context(self.code, ln, cl)
            base = f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} "
            raise SyntaxError(base + (msg or f"Ожидался {kind}('{value}')") + f"\n{ctx}")
        self.advance()
        return v

    def error_ctx_from(self, token_idx=None):
        if token_idx is None:
            k, v, ln, cl = self.cur()
        else:
            if token_idx >= len(self.tokens):
                token_idx = len(self.tokens) - 1
            k, v, ln, cl = self.tokens[token_idx] if self.tokens else (None, None, 1, 1)
        return get_context(self.code, ln or 1, cl or 1)

    # --- выражения ---
    def parse_primary(self):
        """Нижний уровень: числа, строки, ID (+вызовы/индексация), скобки, массив, корень"""
        k, v, ln, cl = self.cur()
        if k is None:
            return None

        if k == 'строченька':
            self.advance()
            return Node('строченька', value=v, line=ln, col=cl)

        if k == 'число':
            self.advance()
            return Node('число', value=v, line=ln, col=cl)

        if k == 'ROOT':
            self.advance()
            expr = self.parse_expression()
            if not expr:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось выражение после 'корень из'\n{self.error_ctx_from(self.i)}")
            return Node('RootOp', children=[expr])

        if k == 'BRACKET' and v == '[':
            # массив
            self.advance()
            elems = []
            while not (self.cur()[0] == 'BRACKET' and self.cur()[1] == ']'):
                elem = self.parse_expression()
                if elem:
                    elems.append(elem)
                if self.cur()[0] == 'COMMA':
                    self.advance()
                elif self.cur()[0] == 'BRACKET' and self.cur()[1] == ']':
                    break
                else:
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалась запятая или ']' в массиве\n{self.error_ctx_from(self.i)}")
            self.expect('BRACKET', ']', msg="Незакрытый массив")
            return Node('Array', children=elems)

        if k == 'PARENTHESIS' and v == '(':
            self.advance()
            expr = self.parse_expression()
            self.expect('PARENTHESIS', ')', msg="Незакрытая скобка")
            return expr

        if k == 'ID':

            if v == 'Истина':
                self.advance()
                return Node('двосуть', value=True, line=ln, col=cl)

            if v == 'Ложь':
                self.advance()
                return Node('двосуть', value=False, line=ln, col=cl)

            # собрать многосоставный идентификатор через DOT
            id_parts = [v]
            ln_id, cl_id = ln, cl
            self.advance()
            while self.cur()[0] == 'DOT':
                self.advance()
                if self.cur()[0] != 'ID':
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался идентификатор после '.'\n{get_context(self.code, ln_id, cl_id)}")
                id_parts.append(self.cur()[1]); self.advance()
            id_value = '.'.join(id_parts)
            node = Node('ID', value=id_value, line=ln_id, col=cl_id)

            if self.cur()[0] == 'PARENTHESIS' and self.cur()[1] == '(':
                self.advance()
                args = self.parse_comma_separated('PARENTHESIS', ')', allow_empty=False, element_parser=self.parse_expression,
                                                 error_msg="Ожидалось выражение в аргументах функции")
                return Node('Call', value=id_value, children=args, line=ln_id, col=cl_id)

            if id_value == 'созвать_дружину' and self.cur()[0] == 'PARENTHESIS' and self.cur()[1] == '(':
                return self.parse_array_create_specific(ln_id, cl_id)

            if self.cur()[0] == 'BRACKET' and self.cur()[1] == '[':
                self.advance()
                idx = self.parse_expression()
                if not idx:
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался индекс после '['\n{get_context(self.code, ln_id, cl_id)}")
                self.expect('BRACKET', ']', msg="Ожидалась ']' после индекса", line=ln_id, col=cl_id)
                return Node('ArrayAccess', children=[node, idx])
            return node

        return None

    def parse_comma_separated(self, close_kind, close_value, allow_empty, element_parser, error_msg):
        """Парсинг списков элементов (аргументы, элементы массива). Возвращает список."""
        elems = []
        if self.cur()[0] == close_kind and self.cur()[1] == close_value:
            self.advance()
            return elems
        while True:
            elem = element_parser()
            if not elem:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} {error_msg}\n{self.error_ctx_from(self.i)}")
            elems.append(elem)
            if self.cur()[0] == 'COMMA':
                self.advance()
                continue
            if self.cur()[0] == close_kind and self.cur()[1] == close_value:
                self.advance()
                break
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалась запятая или '{close_value}'\n{self.error_ctx_from(self.i)}")
        return elems

    def parse_array_create_specific(self, line, col):
        """Парсинг создания массива - созвать_дружину"""

        if self.cur()[0] == 'PARENTHESIS' and self.cur()[1] == '(':
            self.advance()
        size_expr = self.parse_expression()
        if not size_expr:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался размер массива в 'созвать_дружину'\n{get_context(self.code, line, col)}")
        self.expect('COMMA', msg="Ожидалась запятая после размера в 'созвать_дружину'", line=line, col=col)
        value_expr = self.parse_expression()
        if not value_expr:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось значение для заполнения массива в 'созвать_дружину'\n{get_context(self.code, line, col)}")
        self.expect('PARENTHESIS', ')', msg="Ожидалась ')' после аргументов в 'созвать_дружину'", line=line, col=col)
        return Node('ArrayCreate', children=[size_expr, value_expr])

    def parse_left_assoc(self, subparser, ops):
        left = subparser()
        if not left:
            return None
        while self.cur()[0] == 'OP' and self.cur()[1] in ops:
            op = self.cur()[1]
            self.advance()
            right = subparser()
            if not right:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось выражение после '{op}'\n{self.error_ctx_from(self.i-1)}")
            left = Node('BinaryOp', op=op, children=[left, right])
        return left

    def parse_power(self):
        left = self.parse_primary()
        if not left:
            return None

        if self.cur()[0] == 'OP' and self.cur()[1] in ('**', 'возвысить в'):
            op = self.cur()[1]
            self.advance()
            right = self.parse_power()
            if not right:
                raise SyntaxError(
                    f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} "
                    f"Ожидалось выражение после '{op}'\n{self.error_ctx_from(self.i-1)}"
                )
            return Node('BinaryOp', op=op, children=[left, right])

        return left

    def parse_multiplicative(self):
        return self.parse_left_assoc(
            self.parse_power,
            ('*', '/', '%', 'умножи на', 'раздели на', 'остаток от')
        )

    def parse_additive(self):
        return self.parse_left_assoc(
            self.parse_multiplicative,
            ('+', '-', 'прибави', 'отними')
        )

    def parse_comparison(self):
        left = self.parse_additive()
        if not left:
            return None

        if self.cur()[0] == 'OP' and self.cur()[1] in (
            '<', '>', '<=', '>=', '==', '!=',
            'равно', 'не равно',
            'превосходит', 'уступает',
            'ровно либо превосходит',
            'ровно либо уступает'
        ):
            op = self.cur()[1]
            self.advance()
            right = self.parse_additive()
            if not right:
                raise SyntaxError(
                    f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} "
                    f"Ожидалось выражение после '{op}'\n{self.error_ctx_from(self.i-1)}"
                )
            return Node('BinaryOp', op=op, children=[left, right])

        return left

    def parse_not(self):
        """Унарное отрицание 'не' (наивысший приоритет среди логических)."""
        if self.cur()[0] == 'ID' and self.cur()[1] == 'не':
            self.advance()
            operand = self.parse_not()
            return Node('UnaryOp', op='не', children=[operand])
        return self.parse_comparison()

    def parse_and(self):
        """Логическое 'И' (левоассоциативное)."""
        left = self.parse_not()
        while self.cur()[0] == 'ID' and self.cur()[1] == 'и':
            self.advance()
            right = self.parse_not()
            left = Node('BinaryOp', op='и', children=[left, right])
        return left

    def parse_or(self):
        """Логическое 'ИЛИ' (левоассоциативное, низший приоритет)."""
        left = self.parse_and()
        while self.cur()[0] == 'ID' and self.cur()[1] == 'или':
            self.advance()
            right = self.parse_and()
            left = Node('BinaryOp', op='или', children=[left, right])
        return left

    def parse_expression(self):
        """Выражение: логические операторы, сравнения и арифметика."""
        return self.parse_or()

    def parse_expression_statement(self):
        expr = self.parse_expression()
        if expr and self.cur()[0] == 'GOYDA':
            self.advance()
            return Node('ExpressionStatement', children=[expr])
        return None

    def parse_assignment(self):
        start = self.i
        if self.cur()[0] != 'ID':
            return None
        var_name = self.cur()[1]; line, col = self.cur()[2], self.cur()[3]
        var_node = Node('ID', value=var_name, line=line, col=col)
        self.advance()

        # типизация
        type_hint = None
        if self.cur()[0] == 'TYPE_ANNOTATION':
            self.advance()
            if self.cur()[0] != 'ID':
                raise SyntaxError(f"Ожидался тип после 'быти' (строка {line}, столбец {col})")
            # собрать составной тип
            parts = []
            while self.cur()[0] == 'ID' and self.cur()[1] not in ('=', 'гойда'):
                parts.append(self.cur()[1]); self.advance()
            type_name = ' '.join(parts)
            type_hint = TYPE_MAP.get(type_name)
            if type_hint is None:
                raise SyntaxError(f"Неизвестный тип '{type_name}' (строка {line}, столбец {col})")

        # ID[expr] = expr
        if self.cur()[0] == 'BRACKET' and self.cur()[1] == '[':
            self.advance()
            idx = self.parse_expression()
            if not idx:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался индекс после '['\n{get_context(self.code, line, col)}")
            self.expect('BRACKET', ']', msg="Ожидалась ']' после индекса", line=line, col=col)
            if self.cur()[0] == 'ASSIGN':
                self.advance()
                expr = self.parse_expression()
                if self.cur()[0] == 'GOYDA':
                    self.advance()
                    return Node('ArrayAssignment', children=[var_node, idx, expr], type_hint=type_hint, line=line, col=col)
                raise SyntaxError(f"Ожидалась 'гойда' после присваивания\n{get_context(self.code, line, col)}")
            self.i = start
            return None

        # ID = expr
        if self.cur()[0] == 'ASSIGN':
            self.advance()
            expr = self.parse_expression()
            if expr and getattr(expr, 'type', None) == 'число' and type_hint:
                expr.type_hint = type_hint
            if self.cur()[0] == 'GOYDA':
                self.advance()
                return Node('Assignment', children=[var_node, expr], type_hint=type_hint, line=line, col=col)
            raise SyntaxError(f"Ожидалась 'гойда' после присваивания\n{get_context(self.code, line, col)}")

        self.i = start
        return None

    def parse_print(self):
        """Парсинг функции молвить (print) и молвить(... и эхом затихнуть)"""
        if self.cur()[0] != 'ID' or self.cur()[1] != 'молвить':
            return None
        line, col = self.cur()[2], self.cur()[3]; self.advance()

        expr_nodes = []
        if self.cur()[0] == 'PARENTHESIS' and self.cur()[1] == '(':
            self.advance()
            expr_nodes = self.parse_comma_separated('PARENTHESIS', ')', allow_empty=False, element_parser=self.parse_expression,
                                                  error_msg="Ожидалось выражение в 'молвить'")
        else:
            # однотомный вариант: молвить идентификатор
            if self.cur()[0] == "строченька":
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Строки после 'молвить' должны заключаться в ()\n{self.error_ctx_from(self.i)}")
            if self.cur()[0] != 'ID':
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалась переменная после 'молвить'\n{self.error_ctx_from(self.i)}")
            expr_nodes = [Node('ID', value=self.cur()[1], line=self.cur()[2], col=self.cur()[3])]
            self.advance()

        # опция "и эхом затихнуть"
        is_silent = (self.cur()[0] == 'ID' and self.cur()[1] == 'и' and
                     (self.i+2) < len(self.tokens) and self.tokens[self.i+1][0] == 'ID' and self.tokens[self.i+1][1] == 'эхом' and
                     self.tokens[self.i+2][0] == 'ID' and self.tokens[self.i+2][1] == 'затихнуть')
        if is_silent:
            self.advance(); self.advance(); self.advance()

        self.expect('GOYDA', msg="Ожидалась 'гойда' после 'молвить'", line=line, col=col)
        return Node('PrintWithSilence' if is_silent else 'Print', children=expr_nodes, line=line, col=col)

    def parse_input(self):
        """Парсинг функции внемли (input) с опциональным сообщением в скобках"""
        if self.cur()[0] != 'ID' or self.cur()[1] != 'внемли':
            return None
        line, col = self.cur()[2], self.cur()[3]; self.advance()
        self.expect('PARENTHESIS', '(', msg="Ожидалась '(' после 'внемли'", line=line, col=col)

        prompt_node = None
        if self.cur()[0] == 'строченька':
            prompt_node = Node('строченька', value=self.cur()[1].strip('"'), line=self.cur()[2], col=self.cur()[3]); self.advance()
            self.expect('COMMA', msg="Ожидалась запятая ',' после строки", line=line, col=col)

        if self.cur()[0] != 'ID':
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалась переменная\n{self.error_ctx_from(self.i)}")
        var_node = Node('ID', value=self.cur()[1], line=self.cur()[2], col=self.cur()[3]); self.advance()
        self.expect('PARENTHESIS', ')', msg="Ожидалась ')' после переменной", line=line, col=col)
        self.expect('GOYDA', msg="Ожидалась 'гойда' после 'внемли(...)'", line=line, col=col)

        children = [var_node] if not prompt_node else [prompt_node, var_node]
        return Node('Input', children=children, line=line, col=col)

    def parse_while(self):
        """Парсинг цикла покуда (while)"""
        if self.cur()[0] != 'ID' or self.cur()[1] != 'покуда':
            return None
        line, col = self.cur()[2], self.cur()[3]; self.advance()
        condition = self.parse_expression()
        if not condition:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось условие после 'покуда'\n{get_context(self.code, line, col)}")
        self.expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после условия в 'покуда'", line=line, col=col)

        body = []
        while self.cur()[0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
            stmt = self.parse_any_statement_inside_loop()
            if stmt:
                body.append(stmt)
            else:
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Неожиданный токен '{self.cur()[1]}' в теле 'покуда'\n{self.error_ctx_from(self.i)}")
        self.expect('ЗАКРЫТАЯФИГУРНАЯСКОБКА')
        return Node('While', children=[condition, Node('Block', children=body)])

    def parse_array_create(self):
        """Парсинг создания массива - созвать_дружину"""
        if self.cur()[0] != 'ID' or self.cur()[1] != 'созвать_дружину':
            return None
        line, col = self.cur()[2], self.cur()[3]; self.advance()
        self.expect('PARENTHESIS', '(', msg="Ожидалось '(' после 'созвать_дружину'", line=line, col=col)
        size_expr = self.parse_expression()
        if not size_expr:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался размер массива в 'созвать_дружину'\n{get_context(self.code, line, col)}")
        self.expect('COMMA', msg="Ожидалась запятая после размера в 'созвать_дружину'", line=line, col=col)
        value_expr = self.parse_expression()
        if not value_expr:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось значение для заполнения массива в 'созвать_дружину'\n{get_context(self.code, line, col)}")
        self.expect('PARENTHESIS', ')', msg="Ожидалась ')' после аргументов в 'созвать_дружину'", line=line, col=col)
        return Node('ArrayCreate', children=[size_expr, value_expr])

    def parse_if(self):
        """Парсинг условий аще - аще ли - ино (if-elif-else)"""
        if self.cur()[0] != 'ID' or self.cur()[1] != 'аще':
            return None
        line, col = self.cur()[2], self.cur()[3]; self.advance()
        condition = self.parse_expression()
        if not condition:
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось условие после 'аще'\n{get_context(self.code, line, col)}")
        self.expect('ID', 'то', msg="Ожидалось 'то' после условия", line=line, col=col)
        self.expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после 'то'", line=line, col=col)

        def parse_block_until_close(allowed_stmt_parsers):
            body = []
            while self.cur()[0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                stmt = None
                for p in allowed_stmt_parsers:
                    stmt = p()
                    if stmt:
                        body.append(stmt)
                        break
                if not stmt:
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Неожиданный токен '{self.cur()[1]}' в теле\n{self.error_ctx_from(self.i)}")
            self.expect('ЗАКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'закончили пляски' после тела", line=line, col=col)
            return body

        if_body = parse_block_until_close([self.parse_assignment, self.parse_print, self.parse_input, self.parse_while, self.parse_if, self.parse_return, self.parse_fixed_loop])
        # elif branches
        elif_branches = []
        while self.cur()[0] == 'ID' and self.cur()[1] == 'аще':
            self.advance()
            self.expect('ID', 'ли', msg="Ожидалось 'ли' после 'аще' для 'аще ли'", line=line, col=col)
            elif_cond = self.parse_expression()
            self.expect('ID', 'то', msg="Ожидалось 'то' после условия в 'аще ли'", line=line, col=col)
            self.expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после 'то' в 'аще ли'", line=line, col=col)
            elif_body = parse_block_until_close([self.parse_assignment, self.parse_print, self.parse_input, self.parse_while, self.parse_if, self.parse_return])
            elif_branches.append((elif_cond, Node('Block', children=elif_body)))

        else_body = []
        if self.cur()[0] == 'ID' and self.cur()[1] == 'ино':
            self.advance()
            self.expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после 'ино'", line=line, col=col)
            else_body = parse_block_until_close([self.parse_assignment, self.parse_print, self.parse_input, self.parse_while, self.parse_if, self.parse_return, self.parse_fixed_loop])

        return Node('If', children=[
            condition,
            Node('Block', children=if_body),
            Node('ElifBlocks', children=[Node('Elif', children=[cond, block]) for cond, block in elif_branches]),
            Node('Block', children=else_body)
        ])

    def parse_function(self):
        """Парсинг конструкции функции (def)"""
        if self.cur()[0] != 'DEF':
            return None
        line, col = self.cur()[2], self.cur()[3]; self.advance()
        if self.cur()[0] != 'ID':
            raise SyntaxError(f"Ожидалось имя функции после 'сотвори'\n{get_context(self.code, line, col)}")
        func_name = self.cur()[1]; self.advance()
        self.expect('PARENTHESIS', '(', msg="Ожидалось '(' после имени функции", line=line, col=col)

        args = []
        if not (self.cur()[0] == 'PARENTHESIS' and self.cur()[1] == ')'):
            while True:
                if self.cur()[0] != 'ID':
                    raise SyntaxError(f"Ожидалось имя аргумента (получен {self.cur()[0]}: '{self.cur()[1]}')\n{get_context(self.code, line, col)}")
                arg_name = self.cur()[1]; arg_line, arg_col = self.cur()[2], self.cur()[3]; self.advance()
                arg_type = None
                if self.cur()[0] == 'TYPE_ANNOTATION' and self.cur()[1] == 'быти':
                    self.advance()
                    if self.cur()[0] != 'ID':
                        raise SyntaxError(f"Ожидался тип после 'быти'\n{get_context(self.code, arg_line, arg_col)}")
                    parts = []
                    while self.cur()[0] == 'ID' and self.cur()[1] not in ('=', 'гойда', ')', ','):
                        parts.append(self.cur()[1]); self.advance()
                    type_name = ' '.join(parts)
                    arg_type = TYPE_MAP.get(type_name)
                    if arg_type is None:
                        raise SyntaxError(f"Неизвестный тип '{type_name}'\n{get_context(self.code, arg_line, arg_col)}")
                args.append(Node('Arg', value=arg_name, type_hint=arg_type))
                if self.cur()[0] == 'COMMA':
                    self.advance()
                    continue
                break
        self.expect('PARENTHESIS', ')', msg="Ожидалось ')' после аргументов", line=line, col=col)
        self.expect('RETURN_TYPE', msg="Ожидалось 'изречет' после аргументов", line=line, col=col)
        # сбор типа возврата
        if self.cur()[0] != 'ID':
            raise SyntaxError(f"Ожидался тип возврата после 'изречет'\n{get_context(self.code, line, col)}")
        parts = []
        while self.cur()[0] == 'ID' and self.cur()[1] not in ('гойда', 'ухожу я в пляс'):
            parts.append(self.cur()[1]); self.advance()
        return_type = ' '.join(parts)
        if return_type not in TYPE_MAP:
            raise SyntaxError(f"Неизвестный тип возврата '{return_type}'\n{get_context(self.code, line, col)}")
        return_type = TYPE_MAP[return_type]
        self.expect('ОТКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'ухожу я в пляс' после типа возврата", line=line, col=col)

        body = []
        while self.cur()[0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
            stmt = self.parse_any_statement_inside_function()
            if stmt:
                body.append(stmt)
            else:
                raise SyntaxError(f"Неожиданный токен '{self.cur()[1]}' в теле функции\n{self.error_ctx_from(self.i)}")
        self.expect('ЗАКРЫТАЯФИГУРНАЯСКОБКА', msg="Ожидалось 'закончили пляски' после тела функции", line=line, col=col)
        return Node('Function', value=func_name, children=[Node('Args', children=args), Node('Block', children=body)], type_hint=return_type, line=line, col=col)

    def parse_return(self):
        """Парсинг return"""
        if self.cur()[0] != 'RETURN':
            return None
        line, col = self.cur()[2], self.cur()[3]; self.advance()
        expr = self.parse_expression()
        if not expr:
            raise SyntaxError(f"Ожидалось выражение после 'возверни'\n{get_context(self.code, line, col)}")
        if self.cur()[0] == 'GOYDA':
            self.advance()
        return Node('Return', children=[expr])

    def parse_call(self):
        """Парсинг вызова функции"""
        if self.cur()[0] != 'ID':
            return None
        func_name = self.cur()[1]; line, col = self.cur()[2], self.cur()[3]; self.advance()
        if not (self.cur()[0] == 'PARENTHESIS' and self.cur()[1] == '('):
            self.i -= 1
            return None
        self.advance()
        args = self.parse_comma_separated('PARENTHESIS', ')', allow_empty=True, element_parser=self.parse_expression,
                                         error_msg="Ожидалась запятая или ')' в аргументах функции")
        if self.cur()[0] != 'GOYDA':
            raise SyntaxError(f"Ожидалась 'гойда' после вызова функции\n{get_context(self.code, line, col)}")
        self.advance()
        return Node('Call', value=func_name, children=args, line=line, col=col)

    def parse_fixed_loop(self):
        """Парсинг фиксированных циклов Дважды, Трижды, Четырежды"""
        loop_types = {
            'дважды': 2, 'трижды': 3, 'четырежды': 4, 'пятьжды': 5,
            'шестьжды': 6, 'семьжды': 7, 'осьмьжды': 8, 'девятьжды': 9,
            'десятьжды': 10, 'стожды': 100,
        }
        if self.cur()[0] == 'ID' and self.cur()[1].lower() in loop_types:
            loop_name = self.cur()[1].lower(); iterations = loop_types[loop_name]
            line, col = self.cur()[2], self.cur()[3]; self.advance()
            body = []
            if self.cur()[0] == 'ОТКРЫТАЯФИГУРНАЯСКОБКА':
                self.advance()
                while self.cur()[0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                    stmt = (self.parse_assignment() or self.parse_print() or self.parse_input() or self.parse_while()
                            or self.parse_if() or self.parse_fixed_loop() or self.parse_return() or self.parse_call())
                    if stmt:
                        body.append(stmt)
                    else:
                        raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Неожиданный токен '{self.cur()[1]}' в теле '{loop_name}'\n{self.error_ctx_from(self.i)}")
                self.expect('ЗАКРЫТАЯФИГУРНАЯСКОБКА', msg=f"Ожидалось 'закончили пляски' после тела '{loop_name}'", line=line, col=col)
            else:
                stmt = (self.parse_assignment() or self.parse_print() or self.parse_input() or self.parse_while()
                        or self.parse_if() or self.parse_fixed_loop() or self.parse_return() or self.parse_call())
                if not stmt:
                    raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался оператор после '{loop_name}'\n{get_context(self.code, line, col)}")
                body.append(stmt)
            return Node('FixedLoop', value=iterations, children=[Node('Block', children=body)])
        return None

    def parse_import(self):
        """Парсинг конструкции импорта"""
        if self.cur()[0] != 'IMPORT':
            return None
        line, col = self.cur()[2], self.cur()[3]; self.advance()
        if self.cur()[0] != 'строченька':
            raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидалось имя файла в кавычках после 'взять из' или 'прочесть книгу'\n{get_context(self.code, line, col)}")
        filename = self.cur()[1].strip('"'); self.advance()
        alias = None
        if self.cur()[0] in ('AS', 'OLD_AS'):
            self.advance()
            if self.cur()[0] != 'ID':
                raise SyntaxError(f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} Ожидался идентификатор после 'как' или 'и осмыслить текст как'\n{get_context(self.code, line, col)}")
            alias = self.cur()[1]; self.advance()
        self.expect('GOYDA', msg="Ожидалась 'гойда' после конструкции импорта", line=line, col=col)
        if not alias:
            alias = filename.rsplit('.', 1)[0]
        return Node('Import', value=filename, alias=alias, line=line, col=col)

    # --- вспомогательные для использования внутри блоков ---
    def parse_any_statement_inside_loop(self):
        return (self.parse_assignment() or self.parse_print() or self.parse_input() or self.parse_while() or self.parse_if()
                or self.parse_return() or self.parse_fixed_loop())

    def parse_any_statement_inside_function(self):
        return (self.parse_assignment() or self.parse_print() or self.parse_input() or self.parse_while() or self.parse_if()
                or self.parse_function() or self.parse_return() or self.parse_fixed_loop())

    def _sync(self, line):
        """Пропустить токены до смены строки (точка синхронизации для recovery).

        Лексер не выдаёт токенов NEWLINE, поэтому синхронизируемся по номеру
        строки текущего токена.
        """
        while self.i < len(self.tokens) and (self.cur()[2] or 0) == line:
            self.advance()

    # --- основной проход по токенам ---
    def parse(self):
        ast = []
        parsers = (self.parse_if, self.parse_while, self.parse_input, self.parse_print, self.parse_assignment,
                   self.parse_array_create, self.parse_function, self.parse_call, self.parse_fixed_loop, self.parse_import, self.parse_expression_statement)
        while self.i < len(self.tokens):
            if self.cur()[0] is None:
                break
            start = self.i
            s_line, s_col = self.cur()[2], self.cur()[3]
            matched = False
            for p in parsers:
                try:
                    stmt = p()
                except SyntaxError as e:
                    # error-recovery: запомнить ошибку и продолжить со след. строки
                    self.errors.append(e)
                    self._sync(self.cur()[2] or s_line or 1)
                    matched = True
                    break
                if stmt:
                    ast.append(stmt)
                    matched = True
                    break
            if not matched:
                # ни один парсер не принял оператор, начиная с этого токена
                self.errors.append(SyntaxError(
                    f"{Color.RED.value}Оказия синтаксиса:{Color.RESET_ALL.value} "
                    f"Неожиданный токен '{self.tokens[start][1]}'\n"
                    f"{get_context(self.code, s_line or 1, s_col or 1)}"
                ))
                self._sync(s_line or 1)
        return ast


def parse(tokens, code):
    """Построить AST (обратно совместимо: бросает SyntaxError при первой ошибке)."""
    parser = Parser(tokens, code)
    ast = parser.parse()
    if parser.errors:
        raise parser.errors[0]
    return ast


def parse_with_errors(tokens, code):
    """Построить AST и собрать ВСЕ ошибки синтаксиса (для IDE/диагностики).

    Возвращает кортеж (ast, errors), где errors — список исключений SyntaxError.
    """
    parser = Parser(tokens, code)
    ast = parser.parse()
    return ast, list(parser.errors)
