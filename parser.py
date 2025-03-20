from node import Node
from colorama import init, Fore, Style

def get_line_at(code, line_num):
    """Получить строку кода по номеру строки."""
    lines = code.split('\n')
    return lines[line_num - 1] if line_num <= len(lines) else ""


def get_context(code, line_num, col):
    lines = code.split('\n')
    context = []
    if line_num > 1:
        context.append(f"{Fore.CYAN} {line_num-1:3d} | {lines[line_num-2]}{Style.RESET_ALL}")
    context.append(f"{Fore.RED} {line_num:3d} |  {lines[line_num-1]}{Style.RESET_ALL}")
    context.append(f"{Fore.RED}     | {' ' * (col-1)}{Fore.RED}→{Style.RESET_ALL}")
    return "\n".join(context)


def parse(tokens, code):
    i = 0

    def parse_expression():
        nonlocal i
        
        def parse_term():
            nonlocal i
            if i >= len(tokens):
                return None
            kind, value, line, col = tokens[i]
            
            if kind == 'строченька':
                node = Node('строченька', value=value)
                i += 1
                return node
            
            elif kind == 'ID':
                if value == 'созвать_дружину':
                    return parse_array_create()
                node = Node('ID', value=value)
                i += 1
                if i < len(tokens) and tokens[i][0] == 'BRACKET' and tokens[i][1] == '[':
                    i += 1
                    index_node = parse_expression()
                    if not index_node:
                        error_context = get_context(code, line, col)
                        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидался индекс после '['\n{error_context}")
                    if i >= len(tokens) or tokens[i][0] != 'BRACKET' or tokens[i][1] != ']':
                        error_context = get_context(code, line, col)
                        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась ']' после индекса\n{error_context}")
                    i += 1
                    return Node('ArrayAccess', children=[node, index_node])
                return node
            
            elif kind == 'число':
                node = Node('число', value=int(value))
                i += 1
                return node
            
            elif kind == 'ROOT':
                i += 1
                expr_node = parse_expression()
                if not expr_node:
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось выражение после 'корень из'\n{error_context}")
                return Node('RootOp', children=[expr_node])
            
            elif kind == 'BRACKET' and value == '[':
                i += 1
                elements = []
                while i < len(tokens) and not (tokens[i][0] == 'BRACKET' and tokens[i][1] == ']'):
                    element = parse_expression()
                    if element:
                        elements.append(element)
                    if i < len(tokens) and tokens[i][0] == 'COMMA':
                        i += 1
                    elif i < len(tokens) and not (tokens[i][0] == 'BRACKET' and tokens[i][1] == ']'):
                        error_context = get_context(code, line, col)
                        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась запятая или ']' в массиве\n{error_context}")
                if i >= len(tokens) or tokens[i][1] != ']':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Незакрытый массив\n{error_context}")
                i += 1
                return Node('Array', children=elements)
            
            elif kind == 'PARENTHESIS' and value == '(':
                i += 1
                expr_node = parse_expression()
                if i >= len(tokens) or tokens[i][0] != 'PARENTHESIS' or tokens[i][1] != ')':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Незакрытая скобка\n{error_context}")
                i += 1
                return expr_node
            return None

        def parse_factor():
            nonlocal i
            left = parse_term()
            if not left:
                return None
            while i < len(tokens) and tokens[i][0] == 'OP' and tokens[i][1] == '**':
                op = tokens[i][1]
                i += 1
                right = parse_term()
                if not right:
                    error_context = get_context(code, tokens[i-1][2], tokens[i-1][3])
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось выражение после '{op}'\n{error_context}")
                left = Node('BinaryOp', op=op, children=[left, right])
            return left

        def parse_mul_div():
            nonlocal i
            left = parse_factor()
            if not left:
                return None
            while i < len(tokens) and tokens[i][0] == 'OP' and tokens[i][1] in ('*', '/', '%'):
                op = tokens[i][1]
                i += 1
                right = parse_factor()
                if not right:
                    error_context = get_context(code, tokens[i-1][2], tokens[i-1][3])
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось выражение после '{op}'\n{error_context}")
                left = Node('BinaryOp', op=op, children=[left, right])
            return left

        def parse_add_sub():
            nonlocal i
            left = parse_mul_div()
            if not left:
                return None
            while i < len(tokens) and tokens[i][0] == 'OP' and tokens[i][1] in ('+', '-'):
                op = tokens[i][1]
                i += 1
                right = parse_mul_div()
                if not right:
                    error_context = get_context(code, tokens[i-1][2], tokens[i-1][3])
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось выражение после '{op}'\n{error_context}")
                left = Node('BinaryOp', op=op, children=[left, right])
            return left

        return parse_add_sub()
                
        
    def parse_assignment():
        nonlocal i
        start = i
        if i >= len(tokens):
            return None
        if tokens[i][0] == 'ID':
            var_node = Node('ID', value=tokens[i][1])
            line, col = tokens[i][2], tokens[i][3]
            i += 1
            if i < len(tokens) and tokens[i][0] == 'BRACKET' and tokens[i][1] == '[':
                i += 1
                index_node = parse_expression()
                if not index_node:
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидался индекс после '['\n{error_context}")
                if i >= len(tokens) or tokens[i][0] != 'BRACKET' or tokens[i][1] != ']':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась ']' после индекса\n{error_context}")
                i += 1
                if i < len(tokens) and tokens[i][0] == 'ASSIGN':
                    i += 1
                    expr_node = parse_expression()
                    if i < len(tokens) and tokens[i][0] == 'GOYDA':
                        i += 1
                        return Node('ArrayAssignment', children=[var_node, index_node, expr_node])
                    else:
                        error_context = get_context(code, line, col)
                        raise SyntaxError(f"Ожидалась 'гойда' после присваивания\n{error_context}")

            if i < len(tokens) and tokens[i][0] == 'ASSIGN':
                i += 1
                expr_node = parse_expression()
                if i < len(tokens) and tokens[i][0] == 'GOYDA':
                    i += 1
                    return Node('Assignment', children=[var_node, expr_node])
                else:
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"Ожидалась 'гойда' после присваивания\n{error_context}")
        i = start
        return None
    

    def parse_condition():
        nonlocal i
        left = parse_expression()
        if i >= len(tokens):
            return None
        kind, value, line, col = tokens[i]
        if kind == 'OP' and value in ('<', '>', '<=', '>=', '=', '!='):
            op = value
            i += 1
            right = parse_expression()
            if not right:
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось выражение после '{op}'\n{error_context}")
            return Node('Condition', op=op, children=[left, right])
        return None


    def parse_print():
        nonlocal i
        if i >= len(tokens):
            return None
        if tokens[i][0] == 'ID' and tokens[i][1] == 'молвить':
            line, col = tokens[i][2], tokens[i][3]
            i += 1
            
            if i < len(tokens) and tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == '(':
                i += 1
                expr_nodes = []
                while i < len(tokens) and not (tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == ')'):
                    expr_node = parse_expression()
                    if expr_node:
                        expr_nodes.append(expr_node)

                    if i < len(tokens):
                        if tokens[i][0] == 'COMMA':
                            i += 1
                        elif tokens[i][0] != 'PARENTHESIS' or tokens[i][1] != ')':
                            error_context = get_context(code, line, col)
                            raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась ')' после аргумента в 'молвить'\n{error_context}")
                    else:
                        error_context = get_context(code, line, col)
                        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Незакрытая скобка после 'молвить'\n{error_context}")
                if i < len(tokens) and tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == ')':
                    i += 1
                else:
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Незакрытая скобка после 'молвить'\n{error_context}")
            else:
                if i >= len(tokens):
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась переменная после 'молвить'\n{error_context}")
                if tokens[i][0] == "строченька":
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Строки после 'молвить' должны заключаться в ()\n{error_context}")
                if tokens[i][0] != 'ID':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась переменная, а не '{tokens[i][1]}' после 'молвить'\n{error_context}")
                expr_node = Node('ID', value=tokens[i][1])
                i += 1
                expr_nodes = [expr_node]

            if i < len(tokens) and tokens[i][0] == 'GOYDA':
                i += 1
                return Node('Print', children=expr_nodes)
            else:
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась 'гойда' после 'молвить'\n{error_context}")
        return None


    def parse_input():
        nonlocal i
        if i >= len(tokens):
            return None
        if tokens[i][0] == 'ID' and tokens[i][1] == 'внемли':
            line, col = tokens[i][2], tokens[i][3]
            i += 1
            if i < len(tokens) and tokens[i][0] == 'ID':
                var_node = Node('ID', value=tokens[i][1])
                i += 1
                if i < len(tokens) and tokens[i][0] == 'GOYDA':
                    i += 1
                    return Node('Input', children=[var_node])
                else:
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась 'гойда' после 'внемли'\n{error_context}")
            else:
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась переменная после 'внемли'\n{error_context}")
        return None


    def parse_while():
        nonlocal i
        if i >= len(tokens):
            return None
        if tokens[i][0] == 'ID' and tokens[i][1] == 'покуда':
            line, col = tokens[i][2], tokens[i][3]
            i += 1
            condition = parse_condition()
            if not condition:
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось условие после 'покуда'\n{error_context}")
            if i >= len(tokens) or tokens[i][0] != 'ОТКРЫТАЯФИГУРНАЯСКОБКА':
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'ухожу я в пляс' после условия в 'покуда'\n{error_context}")
            i += 1
            body = []

            while i < len(tokens) and tokens[i][0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                stmt = parse_assignment() or parse_print() or parse_input() or parse_while()
                if stmt:
                    body.append(stmt)
                else:
                    if i < len(tokens):
                        error_context = get_context(code, tokens[i][2], tokens[i][3])
                        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Неожиданный токен '{tokens[i][1]}' в теле 'покуда'\n{error_context}")
                    else:
                        error_context = get_context(code, line, col)
                        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась 'закончили пляски' после тела 'покуда'\n{error_context}")
            if i >= len(tokens):
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась 'закончили пляски' после тела 'покуда'\n{error_context}")
            i += 1
            return Node('While', children=[condition, Node('Block', children=body)])
        return None


    def parse_array_create():
        nonlocal i
        if i >= len(tokens):
            return None
        if tokens[i][0] == 'ID' and tokens[i][1] == 'созвать_дружину':
            line, col = tokens[i][2], tokens[i][3]
            i += 1
            if i >= len(tokens) or tokens[i][0] != 'PARENTHESIS' or tokens[i][1] != '(':
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось '(' после 'созвать_дружину'\n{error_context}")
            i += 1
            
            size_expr = parse_expression()
            if not size_expr:
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидался размер массива в 'созвать_дружину'\n{error_context}")
            
            if i >= len(tokens) or tokens[i][0] != 'COMMA':
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась запятая после размера в 'созвать_дружину'\n{error_context}")
            i += 1
            
            value_expr = parse_expression()
            if not value_expr:
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось значение для заполнения массива в 'созвать_дружину'\n{error_context}")
            
            if i >= len(tokens) or tokens[i][0] != 'PARENTHESIS' or tokens[i][1] != ')':
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась ')' после аргументов в 'созвать_дружину'\n{error_context}")
            i += 1
            
            return Node('ArrayCreate', children=[size_expr, value_expr])
        return None


    ast = []
    while i < len(tokens):
        kind, value, line, col = tokens[i]
        if kind == 'NEWLINE':
            i += 1
            continue
        stmt = parse_while()
        if stmt:
            ast.append(stmt)
            continue
        stmt = parse_input()
        if stmt:
            ast.append(stmt)
            continue
        stmt = parse_print()
        if stmt:
            ast.append(stmt)
            continue
        stmt = parse_assignment()
        if stmt:
            ast.append(stmt)
            continue
        stmt = parse_array_create()
        if stmt:
            ast.append(stmt)
            continue
        error_context = get_context(code, line, col)
        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Неожиданный токен '{value}'\n{error_context}")

    return ast