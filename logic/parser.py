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
                node = Node('ID', value=value)
                i += 1
                if i < len(tokens) and tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == '(':
                    i += 1
                    args = []
                    while i < len(tokens) and not (tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == ')'):
                        arg = parse_expression()
                        if arg:
                            args.append(arg)
                        if i < len(tokens) and tokens[i][0] == 'COMMA':
                            i += 1
                        elif i < len(tokens) and not (tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == ')'):
                            error_context = get_context(code, line, col)
                            raise SyntaxError(f"Ожидалась запятая или ')' в аргументах функции\n{error_context}")
                    if i >= len(tokens) or tokens[i][1] != ')':
                        error_context = get_context(code, line, col)
                        raise SyntaxError(f"Ожидалась ')' после аргументов функции\n{error_context}")
                    i += 1
                    return Node('Call', value=value, children=args, line=line, col=col)
                elif value == 'созвать_дружину':
                    return parse_array_create()
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
                node = Node('число', value=value, line=line, col=col)
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
            var_name = tokens[i][1]
            line, col = tokens[i][2], tokens[i][3]
            var_node = Node('ID', value=var_name, line=line, col=col)
            i += 1
            type_hint = None
            if i < len(tokens) and tokens[i][0] == 'TYPE_ANNOTATION':
                i += 1
                if i < len(tokens) and tokens[i][0] == 'ID':
                    type_parts = []
                    while i < len(tokens) and tokens[i][0] == 'ID' and tokens[i][1] not in ('=', 'гойда'):
                        type_parts.append(tokens[i][1])
                        i += 1
                    type_name = ' '.join(type_parts)
                    type_map = {
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
                    type_hint = type_map.get(type_name)
                    if type_hint is None:
                        raise SyntaxError(f"Неизвестный тип '{type_name}' (строка {line}, столбец {col})")
                else:
                    raise SyntaxError(f"Ожидался тип после 'быти' (строка {line}, столбец {col})")

            # ID[expression] = expression
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
                        return Node('ArrayAssignment', children=[var_node, index_node, expr_node], type_hint=type_hint, line=line, col=col)
                    else:
                        error_context = get_context(code, line, col)
                        raise SyntaxError(f"Ожидалась 'гойда' после присваивания\n{error_context}")
                i = start
                return None

            # ID = expression
            if i < len(tokens) and tokens[i][0] == 'ASSIGN':
                i += 1
                expr_node = parse_expression()
                if expr_node and expr_node.type == 'число' and type_hint:
                    expr_node.type_hint = type_hint
                if i < len(tokens) and tokens[i][0] == 'GOYDA':
                    i += 1
                    return Node('Assignment', children=[var_node, expr_node], type_hint=type_hint, line=line, col=col)
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
        if kind == 'OP' and value in ('<', '>', '<=', '>=', '==', '!='):
            op = value
            i += 1
            right = parse_expression()
            if not right:
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось выражение после '{op}'\n{error_context}")
            return Node('Condition', op=op, children=[left, right])
        return None


    def parse_print():
        """Парсинг функции молвить (print)"""
        nonlocal i
        if i >= len(tokens):
            return None
        if tokens[i][0] == 'ID' and tokens[i][1] == 'молвить':
            line, col = tokens[i][2], tokens[i][3]
            i += 1
            
            if i < len(tokens) and tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == '(':
                i += 1
                expr_nodes = []
                if i < len(tokens) and not (tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == ')'):
                    expr_node = parse_expression()
                    if not expr_node:
                        error_context = get_context(code, line, col)
                        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось выражение в 'молвить'\n{error_context}")
                    expr_nodes.append(expr_node)
                    while i < len(tokens) and tokens[i][0] == 'COMMA':
                        i += 1
                        next_expr = parse_expression()
                        if not next_expr:
                            error_context = get_context(code, line, col)
                            raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось выражение после запятой в 'молвить'\n{error_context}")
                        expr_nodes.append(next_expr)
                if i >= len(tokens) or tokens[i][0] != 'PARENTHESIS' or tokens[i][1] != ')':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалась ')' после аргументов в 'молвить'\n{error_context}")
                i += 1
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
        """Парсинг функции внемли (input)"""
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
        """Парсинг цикла покуда (while)"""
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
                stmt = (parse_assignment() or parse_print() or parse_input() or 
                    parse_while() or parse_if() or parse_return() or parse_fixed_loop())
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
        """Парсинг создания массива - созвать_дружину"""
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
    

    def parse_if():
        """Парсинг условий аще - аще ли - ино (if-elif-else)"""
        nonlocal i
        if i >= len(tokens):
            return None
        if tokens[i][0] == 'ID' and tokens[i][1] == 'аще':
            line, col = tokens[i][2], tokens[i][3]
            i += 1
            
            condition = parse_condition()
            if not condition:
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось условие после 'аще'\n{error_context}")
            
            if i >= len(tokens) or tokens[i][0] != 'ID' or tokens[i][1] != 'то':
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'то' после условия\n{error_context}")
            i += 1
            
            if i >= len(tokens) or tokens[i][0] != 'ОТКРЫТАЯФИГУРНАЯСКОБКА':
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'ухожу я в пляс' после 'то'\n{error_context}")
            i += 1
            
            if_body = []
            while i < len(tokens) and tokens[i][0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                stmt = (parse_assignment() or parse_print() or parse_input() or 
                    parse_while() or parse_if() or parse_return())
                if stmt:
                    if_body.append(stmt)
                else:
                    if i < len(tokens):
                        error_context = get_context(code, tokens[i][2], tokens[i][3])
                        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Неожиданный токен '{tokens[i][1]}' в теле 'аще'\n{error_context}")
                    break
            if i >= len(tokens) or tokens[i][0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                error_context = get_context(code, line, col)
                raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'закончили пляски' после тела 'аще'\n{error_context}")
            i += 1
            
            elif_branches = []
            while i < len(tokens) and tokens[i][0] == 'ID' and tokens[i][1] == 'аще':
                i += 1
                if i >= len(tokens) or tokens[i][0] != 'ID' or tokens[i][1] != 'ли':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'ли' после 'аще' для 'аще ли'\n{error_context}")
                i += 1
                elif_condition = parse_condition()
                if not elif_condition:
                    error_context = get_context(code, tokens[i-1][2], tokens[i-1][3])
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось условие после 'аще ли'\n{error_context}")
                if i >= len(tokens) or tokens[i][0] != 'ID' or tokens[i][1] != 'то':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'то' после условия в 'аще ли'\n{error_context}")
                i += 1
                if i >= len(tokens) or tokens[i][0] != 'ОТКРЫТАЯФИГУРНАЯСКОБКА':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'ухожу я в пляс' после 'то' в 'аще ли'\n{error_context}")
                i += 1
                elif_body = []
                while i < len(tokens) and tokens[i][0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                    stmt = (parse_assignment() or parse_print() or parse_input() or 
                    parse_while() or parse_if() or parse_return())
                    if stmt:
                        elif_body.append(stmt)
                    else:
                        if i < len(tokens):
                            error_context = get_context(code, tokens[i][2], tokens[i][3])
                            raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Неожиданный токен '{tokens[i][1]}' в теле 'аще ли'\n{error_context}")
                        break
                if i >= len(tokens) or tokens[i][0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'закончили пляски' после тела 'аще ли'\n{error_context}")
                i += 1
                elif_branches.append((elif_condition, Node('Block', children=elif_body)))
            
            else_body = []
            if i < len(tokens) and tokens[i][0] == 'ID' and tokens[i][1] == 'ино':
                i += 1
                if i >= len(tokens) or tokens[i][0] != 'ОТКРЫТАЯФИГУРНАЯСКОБКА':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'ухожу я в пляс' после 'ино'\n{error_context}")
                i += 1
                while i < len(tokens) and tokens[i][0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                    stmt = (parse_assignment() or parse_print() or parse_input() or 
                    parse_while() or parse_if() or parse_return() or parse_fixed_loop())
                    if stmt:
                        else_body.append(stmt)
                    else:
                        if i < len(tokens):
                            error_context = get_context(code, tokens[i][2], tokens[i][3])
                            raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Неожиданный токен '{tokens[i][1]}' в теле 'ино'\n{error_context}")
                        break
                if i >= len(tokens) or tokens[i][0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'закончили пляски' после тела 'ино'\n{error_context}")
                i += 1
            
            return Node('If', children=[
                condition,
                Node('Block', children=if_body),
                Node('ElifBlocks', children=[Node('Elif', children=[cond, block]) for cond, block in elif_branches]),
                Node('Block', children=else_body)
            ])
        return None
    

    def parse_function():
        """Парсинг конструкции функции (def)"""
        nonlocal i
        if i >= len(tokens) or tokens[i][0] != 'DEF':
            return None
        line, col = tokens[i][2], tokens[i][3]
        i += 1

        if i >= len(tokens) or tokens[i][0] != 'ID':
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидалось имя функции после 'сотвори'\n{error_context}")
        func_name = tokens[i][1]
        i += 1

        if i >= len(tokens) or tokens[i][0] != 'PARENTHESIS' or tokens[i][1] != '(':
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидалось '(' после имени функции\n{error_context}")
        i += 1

        args = []
        while i < len(tokens) and not (tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == ')'):
            if tokens[i][0] == 'ID':
                arg_name = tokens[i][1]
                arg_line, arg_col = tokens[i][2], tokens[i][3]
                i += 1
                type_hint = None
                if i < len(tokens) and tokens[i][0] == 'TYPE_ANNOTATION' and tokens[i][1] == 'быти':
                    i += 1
                    if i >= len(tokens) or tokens[i][0] != 'ID':
                        error_context = get_context(code, arg_line, arg_col)
                        raise SyntaxError(f"Ожидался тип после 'быти'\n{error_context}")
                    type_parts = []
                    while (i < len(tokens) and tokens[i][0] == 'ID' and 
                        tokens[i][1] not in ('=', 'гойда', ')', ',')):
                        type_parts.append(tokens[i][1])
                        i += 1
                    type_name = ' '.join(type_parts)
                    type_map = {
                        'цело': 'число:int',
                        'плывун': 'число:float',
                        'строченька': 'строченька',
                        'двосуть': 'двосуть'
                    }
                    type_hint = type_map.get(type_name)
                    if type_hint is None:
                        error_context = get_context(code, arg_line, arg_col)
                        raise SyntaxError(f"Неизвестный тип '{type_name}'\n{error_context}")
                
                args.append(Node('Arg', value=arg_name, type_hint=type_hint))
                
                if i < len(tokens) and tokens[i][0] == 'COMMA':
                    i += 1
                elif i < len(tokens) and tokens[i][1] != ')':
                    error_context = get_context(code, arg_line, arg_col)
                    raise SyntaxError(f"Ожидалась ',' или ')' после аргумента\n{error_context}")
            else:
                error_context = get_context(code, line, col)
                raise SyntaxError(f"Ожидалось имя аргумента (получен {tokens[i][0]}: '{tokens[i][1]}')\n{error_context}")
        
        if i >= len(tokens) or tokens[i][1] != ')':
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидалось ')' после аргументов\n{error_context}")
        i += 1

        if i >= len(tokens) or tokens[i][0] != 'RETURN_TYPE':
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидалось 'изречет' после аргументов\n{error_context}")
        i += 1

        if i >= len(tokens) or tokens[i][0] != 'ID':
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидался тип возврата после 'изречет'\n{error_context}")
        return_type = tokens[i][1]
        type_map = {
            'цело': 'число:int',
            'плывун': 'число:float',
            'строченька': 'строченька',
            'двосуть': 'двосуть'
        }
        if return_type not in type_map:
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Неизвестный тип возврата '{return_type}'\n{error_context}")
        return_type = type_map[return_type]
        i += 1

        if i >= len(tokens) or tokens[i][0] != 'ОТКРЫТАЯФИГУРНАЯСКОБКА':
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидалось 'ухожу я в пляс' после типа возврата\n{error_context}")
        i += 1
        
        body = []
        while i < len(tokens) and tokens[i][0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
            stmt = (parse_assignment() or parse_print() or parse_input() or 
                    parse_while() or parse_if() or parse_function() or parse_return() or parse_fixed_loop())
            if stmt:
                body.append(stmt)
            else:
                if i < len(tokens):
                    error_context = get_context(code, tokens[i][2], tokens[i][3])
                    raise SyntaxError(f"Неожиданный токен '{tokens[i][1]}' в теле функции\n{error_context}")
                break
        if i >= len(tokens):
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидалось 'закончили пляски' после тела функции\n{error_context}")
        i += 1

        return Node('Function', value=func_name, children=[Node('Args', children=args), 
                                                        Node('Block', children=body)], type_hint=return_type)
    

    def parse_return():
        """Парсинг return"""
        nonlocal i
        if i >= len(tokens) or tokens[i][0] != 'RETURN':
            return None
        line, col = tokens[i][2], tokens[i][3]
        i += 1

        expr = parse_expression()
        if not expr:
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидалось выражение после 'возверни'\n{error_context}")
        
        if i < len(tokens) and tokens[i][0] == 'GOYDA':
            i += 1
        return Node('Return', children=[expr])
    

    def parse_call():
        """Парсинг вызова функции"""
        nonlocal i
        if i >= len(tokens) or tokens[i][0] != 'ID':
            return None
        func_name = tokens[i][1]
        line, col = tokens[i][2], tokens[i][3]
        i += 1
        
        if i >= len(tokens) or tokens[i][0] != 'PARENTHESIS' or tokens[i][1] != '(':
            i -= 1
            return None
        
        i += 1
        args = []
        while i < len(tokens) and not (tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == ')'):
            arg = parse_expression()
            if arg:
                args.append(arg)
            if i < len(tokens) and tokens[i][0] == 'COMMA':
                i += 1
            elif i < len(tokens) and not (tokens[i][0] == 'PARENTHESIS' and tokens[i][1] == ')'):
                error_context = get_context(code, line, col)
                raise SyntaxError(f"Ожидалась запятая или ')' в аргументах функции\n{error_context}")
        
        if i >= len(tokens) or tokens[i][1] != ')':
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидалась ')' после аргументов функции\n{error_context}")
        i += 1
        
        if i >= len(tokens) or tokens[i][0] != 'GOYDA':
            error_context = get_context(code, line, col)
            raise SyntaxError(f"Ожидалась 'гойда' после вызова функции\n{error_context}")
        i += 1
        
        return Node('Call', value=func_name, children=args, line=line, col=col)
    

    def parse_fixed_loop():
        """Парсинг фиксированных циклов Дважды, Трижды, Четырежды"""
        nonlocal i
        if i >= len(tokens):
            return None
        
        loop_types = {
            'дважды': 2,
            'трижды': 3,
            'четырежды': 4,
            'пятьжды': 5,
            'шестьжды': 6,
            'семьжды': 7,
            'осьмьжды': 8,
            'девятьжды': 9,
            'десятьжды': 10,
            'стожды': 100,
        }
        
        if tokens[i][0] == 'ID' and tokens[i][1].lower() in loop_types:
            loop_name = tokens[i][1].lower()
            iterations = loop_types[loop_name]
            line, col = tokens[i][2], tokens[i][3]
            i += 1
            
            body = []
            
            # Блок кода в фигурных скобках
            if i < len(tokens) and tokens[i][0] == 'ОТКРЫТАЯФИГУРНАЯСКОБКА':
                i += 1
                while i < len(tokens) and tokens[i][0] != 'ЗАКРЫТАЯФИГУРНАЯСКОБКА':
                    stmt = (parse_assignment() or parse_print() or parse_input() or 
                            parse_while() or parse_if() or parse_fixed_loop() or parse_return() or parse_call())
                    if stmt:
                        body.append(stmt)
                    else:
                        if i < len(tokens):
                            error_context = get_context(code, tokens[i][2], tokens[i][3])
                            raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Неожиданный токен '{tokens[i][1]}' в теле '{loop_name}'\n{error_context}")
                        else:
                            error_context = get_context(code, line, col)
                            raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'закончили пляски' после тела '{loop_name}'\n{error_context}")
                if i >= len(tokens):
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидалось 'закончили пляски' после тела '{loop_name}'\n{error_context}")
                i += 1
            
            # Одиночный оператор
            else:
                stmt = (parse_assignment() or parse_print() or parse_input() or 
                        parse_while() or parse_if() or parse_fixed_loop() or parse_return() or parse_call())
                if stmt:
                    body.append(stmt)
                else:
                    error_context = get_context(code, line, col)
                    raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Ожидался оператор после '{loop_name}'\n{error_context}")
            
            return Node('FixedLoop', value=iterations, children=[Node('Block', children=body)])
        return None


    ast = []
    while i < len(tokens):
        kind, value, line, col = tokens[i]
        if kind == 'NEWLINE':
            i += 1
            continue
        stmt = parse_if()
        if stmt:
            ast.append(stmt)
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
        stmt = parse_function()
        if stmt:
            ast.append(stmt)
            continue
        stmt = parse_call()
        if stmt:
            ast.append(stmt)
            continue
        stmt = parse_fixed_loop()
        if stmt:
            ast.append(stmt)
            continue
        error_context = get_context(code, line, col)
        raise SyntaxError(f"{Fore.RED}Оказия синтаксиса:{Style.RESET_ALL} Неожиданный токен '{value}'\n{error_context}")

    return ast