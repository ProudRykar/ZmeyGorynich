from colorama import Fore, Style
from parser import parse
import decimal
import math
from decimal import Decimal, getcontext
import os
from lexer import tokenize

# TODO: Отрефакторить это говно как-нибудь, но это в далёком будущем я на файлы всё разобью, а то потом сидеть и плакать, 
# лазая по файлам, где я находится говно, ломающее логику

DEBUG = False

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

getcontext().prec = 100

def get_type_name(value):
    if isinstance(value, bool):
        return "двосуть"
    elif isinstance(value, str):
        return "строченька"
    elif isinstance(value, int):
        return "цело"
    elif isinstance(value, float):
        return "плывун"
    elif isinstance(value, Decimal) and getcontext().prec == 30:
        return "плывун малый точный"
    elif isinstance(value, Decimal) and getcontext().prec == 50:
        return "плывун великий"
    elif isinstance(value, Decimal) and getcontext().prec == 100:
        return "плывун звёздный"

    elif isinstance(value, list):
        if not value:
            return "список"
        first_item = value[0]
        if isinstance(first_item, int):
            return "список цело"
        elif isinstance(first_item, float):
            return "список плывун"
        elif isinstance(first_item, str):
            return "список строченька"
        elif isinstance(first_item, bool):
            return "список двосуть"
        elif isinstance(first_item, Decimal):
            return "список плывун малый точный"
        return "список"
    return str(type(value).__name__)

def map_type_hint_to_display_name(type_hint, value):
    if type_hint == 'двосуть':
        return "двосуть"
    elif type_hint == 'строченька':
        return "строченька"
    elif type_hint == 'число:int':
        return "цело"
    elif type_hint == 'число:float':
        return "плывун"
    elif type_hint.startswith('decimal:'):
        prec = int(type_hint.split(':')[1])
        if prec == 30:
            return "плывун малый точный"
        elif prec == 50:
            return "плывун великий"
        elif prec == 100:
            return "плывун звёздный"
    elif type_hint.startswith('list:'):
        element_type = type_hint.split(':', 1)[1]
        element_display_name = map_type_hint_to_display_name(element_type, None)
        return f"список {element_display_name}"
    elif type_hint.startswith('список '):
        element_type = type_hint.split(' ')[1]
        element_display_name = map_type_hint_to_display_name(element_type, None)
        return f"список {element_display_name}"
    return get_type_name(value)

def stringify_value(value):
    if isinstance(value, bool):
        return "Истина" if value else "Ложь"
    return str(value)

builtins = {
    'созвать_дружину': {
        'args': ['size', 'value'],
        'body': None,
        'return_type': 'list:число:int',
        'builtin': lambda size, value, context=None: [value] * int(size)
    },
    'имя_аргумента': {
        'builtin': lambda context=None: context.get_call_arg_name() if context else "неизвестно"
    },
    'тип_значения': {
        'builtin': lambda value, context=None: (
            map_type_hint_to_display_name(
                context.type_hints.get(context.get_call_arg_name(), None),
                value
            )
            if context and context.get_call_arg_name() in context.type_hints
            else get_type_name(value)
        )
    },
    'строчить_значение': {
        'builtin': lambda value, context=None: stringify_value(value)
    },
    'глас': {
        'builtin': lambda value, context=None, arg_type=None: (
            name := context.get_call_arg_name(),
            type_name := (
                map_type_hint_to_display_name(
                    context.type_hints.get(name, None),
                    value
                )
                if context and name in context.type_hints
                else get_type_name(value)
            ),
            is_function_call := (arg_type == 'Call'),
            func_name := context.call_stack[-1]['args_nodes'][0].value if is_function_call else name,
            args_nodes := context.call_stack[-1]['args_nodes'][0].children if is_function_call else [],
            args_values := (
                [evaluate_expression(arg_node, context) for arg_node in args_nodes]
                if is_function_call
                else []
            ),
            args_with_types := [],
            ([
                args_with_types.append((
                    arg_node.value if arg_node.type == 'ID' else str(arg_value),
                    arg_value,
                    (
                        map_type_hint_to_display_name(
                            context.type_hints.get(arg_node.value, None),
                            arg_value
                        )
                        if arg_node.type == 'ID' and arg_node.value in context.type_hints
                        else get_type_name(arg_value)
                    )
                ))
                for arg_node, arg_value in zip(args_nodes, args_values)
            ] if is_function_call else []),
            all_same_type := len(set(arg[2] for arg in args_with_types)) == 1 if args_with_types else False,
            args_str := (
                f"{Fore.BLUE}{', '.join(str(arg[1]) for arg in args_with_types)}{Style.RESET_ALL} быти {Fore.YELLOW}{args_with_types[0][2]}"
                if all_same_type and args_with_types
                else ', '.join(f"{Fore.BLUE}{arg[1]}{Style.RESET_ALL} быти {Fore.YELLOW}{arg[2]}" for arg in args_with_types)
            ) if is_function_call else f"{Fore.BLUE}{stringify_value(value)}{Style.RESET_ALL} быти {Fore.YELLOW}{type_name}{Style.RESET_ALL}",
            call_name := (
                f"{func_name}({', '.join(stringify_value(arg) for arg in args_values)})"
                if is_function_call
                else name
            ),
            result := (
                f"{Fore.CYAN}ᚨᛇᛟ: "  # ᚨᛇᛟ = Духовное знание предков
                f"{Fore.MAGENTA if is_function_call else Fore.GREEN}{call_name}{Style.RESET_ALL} -> "
                f"{Fore.GREEN}{args_str}{Style.RESET_ALL}"
                + (f" -> {Fore.BLUE}{stringify_value(value)}{Style.RESET_ALL} быти {Fore.YELLOW}{type_name}{Style.RESET_ALL}" if is_function_call else "")
            ),
            print(result),
            result
        )[-1]
    },
    'молвить': {
        'builtin': lambda value, context=None: print(value)
    }
}

class Context:
    def __init__(self, parent=None):
        self.variables = {}
        self.type_hints = {}
        self.functions = {}
        self.parent = parent
        self.call_stack = []

    def get(self, key, default=None):
        if key in self.variables:
            return self.variables[key]
        if self.parent:
            return self.parent.get(key, default)
        return default

    def set(self, key, value, type_hint=None):
        self.variables[key] = value
        if type_hint:
            self.type_hints[key] = type_hint

    def set_function(self, name, args, body, return_type):
        self.functions[name] = {'args': args, 'body': body, 'return_type': return_type}
        debug_print(f"Добавлена функция в functions: {name}, текущие функции: {self.functions.keys()}")

    def get_function(self, name):
        if name in self.functions:
            return self.functions[name]
        if name in builtins:
            return builtins[name]
        if self.parent:
            return self.parent.get_function(name)
        return None

    def __setitem__(self, key, value):
        self.variables[key] = value

    def __getitem__(self, key):
        return self.variables[key]

    def push_call(self, func_name, args_nodes, args_values):
        self.call_stack.append({
            'func_name': func_name,
            'args_nodes': args_nodes,
            'args_values': args_values
        })

    def pop_call(self):
        if self.call_stack:
            self.call_stack.pop()

    def get_call_arg_name(self, index=0):
        if not self.call_stack or index >= len(self.call_stack[-1]['args_nodes']):
            return "неизвестно"
        arg_node = self.call_stack[-1]['args_nodes'][index]
        if arg_node.type == 'ID':
            return arg_node.value
        elif arg_node.type == 'Call':
            return f"{arg_node.value}(...)"
        elif arg_node.type == 'двосуть':
            return "истина" if arg_node.value else "ложь"
        else:
            return str(self.call_stack[-1]['args_values'][index])

def evaluate_expression(node, context):
    if node.type == 'строченька':
        return node.value.strip('"')
    
    elif node.type == 'число':
        value = node.value
        if hasattr(node, 'type_hint') and node.type_hint:
            if node.type_hint.startswith('decimal:'):
                return Decimal(value)
            elif node.type_hint == 'число:int':
                return int(value)
            elif node.type_hint == 'число:float':
                return float(value)
        return float(value) if '.' in value else int(value)
    
    elif node.type == 'двосуть':
        return node.value
    
    elif node.type == 'ID':
        parts = node.value.split('.')
        if len(parts) > 1:
            module_name = parts[0]
            if module_name not in context.variables:
                raise NameError(f"Модуль '{module_name}' не найден (строка {node.line}, столбец {node.col})")
            module_vars = context.variables[module_name]
            if not isinstance(module_vars, dict):
                raise NameError(f"'{module_name}' не является модулем (строка {node.line}, столбец {node.col})")

            var_name = parts[1]
            if var_name in module_vars:
                return module_vars[var_name]
            raise NameError(f"Переменная '{var_name}' не найдена в модуле '{module_name}' (строка {node.line}, столбец {node.col})")
        
        if node.value in context.variables:
            return context[node.value]
        func = context.get_function(node.value)
        if func and hasattr(node, 'args'):
            return call_function(func, [evaluate_expression(arg, context) for arg in node.args], context)
        raise NameError(f"Переменная или функция '{node.value}' не определена (строка {node.line}, столбец {node.col})")
    
    elif node.type == 'Array':
        return [evaluate_expression(child, context) for child in node.children]
        
    elif node.type == 'ArrayAccess':
        array = evaluate_expression(node.children[0], context)
        index = evaluate_expression(node.children[1], context)
        if not isinstance(array, list):
            raise ValueError(f"Индексация возможна только для массивов, а не для {type(array).__name__} (строка {node.line}, столбец {node.col})")
        if not isinstance(index, (int, Decimal)) or index < 0 or index >= len(array):
            raise ValueError(f"Недопустимый индекс {index} для массива длиной {len(array)} (строка {node.line}, столбец {node.col})")
        return array[int(index)]
    
    elif node.type == 'ArrayCreate':
        size = evaluate_expression(node.children[0], context)
        value = evaluate_expression(node.children[1], context)
        if not isinstance(size, (int, float, Decimal)) or size < 0:
            raise ValueError(f"Размер массива должен быть неотрицательным числом, а не {size} (строка {node.line}, столбец {node.col})")
        array = [value] * int(size)
        if hasattr(node, 'type_hint') and node.type_hint:
            for item in array:
                check_type(item, node.type_hint, node)
        return array

    elif node.type == 'BinaryOp':
        left = evaluate_expression(node.children[0], context)
        right = evaluate_expression(node.children[1], context)
        
        if node.op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            if isinstance(left, (int, float, Decimal)) and isinstance(right, (int, float, Decimal)):
                if isinstance(left, Decimal) or isinstance(right, Decimal):
                    return Decimal(str(left)) + Decimal(str(right))
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            raise ValueError(f"Нельзя сложить {type(left).__name__} и {type(right).__name__} с помощью '+' (строка {node.line}, столбец {node.col})")
        
        if not (isinstance(left, (int, float, Decimal)) and isinstance(right, (int, float, Decimal))):
            raise ValueError(f"Операция '{node.op}' поддерживается только для чисел, а не для {type(left).__name__} и {type(right).__name__} (строка {node.line}, столбец {node.col})")
        
        if isinstance(left, Decimal) or isinstance(right, Decimal):
            left = Decimal(str(left))
            right = Decimal(str(right))
        
        ops = {
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '%': lambda x, y: x % y,
            '**': lambda x, y: x ** y,
        }
        operation = ops.get(node.op)
        if operation:
            return operation(left, right)
        return None
    
    elif node.type == 'RootOp':
        value = evaluate_expression(node.children[0], context)
        if not isinstance(value, (int, float, Decimal)):
            raise ValueError(f"Корень можно извлечь только из числа, а не из {type(value).__name__} (строка {node.line}, столбец {node.col})")
        if value < 0:
            raise ValueError(f"Корень нельзя извлечь из отрицательного числа {value} (строка {node.line}, столбец {node.col})")
        if isinstance(value, Decimal):
            root_value = Decimal(str(value)).sqrt()
        else:
            root_value = math.sqrt(value)
        if isinstance(root_value, float) and root_value.is_integer():
            return int(root_value)
        return root_value

    elif node.type == 'Call':
        func = context.get_function(node.value)
        if not func:
            raise NameError(f"Функция '{node.value}' не определена (строка {node.line}, столбец {node.col})")
        args = [evaluate_expression(arg, context) for arg in node.children]
        if 'builtin' in func:
            return func['builtin'](*args, context=context)
        else:
            return call_function({'name': node.value, 'args': func['args'], 'body': func['body'], 'args_nodes': node.children}, args, context)

def evaluate_condition(node, context):
    if node.type == 'Condition':
        left = evaluate_expression(node.children[0], context)
        right = evaluate_expression(node.children[1], context)
        ops = {
            '<': lambda x, y: x < y,
            '>': lambda x, y: x > y,
            '<=': lambda x, y: x <= y,
            '>=': lambda x, y: x >= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '===': lambda x, y: x == y,
        }
        operation = ops.get(node.op)
        if operation:
            return operation(left, right)
        raise ValueError(f"Неизвестная операция условия: {node.op} (строка {node.line}, столбец {node.col})")
    return False

def check_type(value, type_hint, node):
    if type_hint is None:
        return
    
    error_loc = f"(строка {node.line if node else '?'}, столбец {node.col if node else '?'})"
    
    if type_hint == 'строченька':
        if not isinstance(value, str):
            raise TypeError(f"Значение должно быть строченькой, а не {type(value).__name__} {error_loc}")
    
    elif type_hint.startswith('число'):
        if not isinstance(value, (int, float, Decimal)):
            raise TypeError(f"Значение должно быть числом, а не {type(value).__name__} {error_loc}")
        if ':' in type_hint:
            subtype = type_hint.split(':')[1]
            if subtype == 'int' and not isinstance(value, int):
                raise TypeError(f"Значение должно быть целым числом (цело), а не {type(value).__name__} {error_loc}")
            elif subtype == 'float' and not isinstance(value, (float, int)):
                raise TypeError(f"Значение должно быть числом с плавающей точкой (плывун), а не {type(value).__name__} {error_loc}")
    
    elif type_hint.startswith('список '):
        if not isinstance(value, list):
            raise TypeError(f"Значение должно быть списком, а не {type(value).__name__} (строка {node.line}, столбец {node.col})")
        element_type = type_hint.split(' ')[1]
        for item in value:
            check_type(item, element_type, node)
    
    elif type_hint.startswith('list:'):
        if not isinstance(value, list):
            raise TypeError(f"Значение должно быть списком, а не {type(value).__name__} (строка {node.line}, столбец {node.col})")
        element_type = type_hint.split(':', 1)[1]
        for item in value:
            check_type(item, element_type, node)
    
    elif type_hint.startswith('decimal:'):
        if not isinstance(value, Decimal):
            raise TypeError(f"Значение должно быть числом высокой точности (decimal), а не {type(value).__name__} (строка {node.line}, столбец {node.col})")
    
    elif type_hint == 'двосуть':
        if not isinstance(value, bool):
            raise TypeError(f"Значение должно быть двосутью (истина или ложь), а не {type(value).__name__} (строка {node.line}, столбец {node.col})")

def call_function(func, args, parent_context):
    if len(args) != len(func['args']):
        raise ValueError(f"Функция '{func.get('name', 'неизвестная')}' ожидает {len(func['args'])} аргументов, получено {len(args)}")
    local_context = Context(parent=parent_context)
    local_context.functions = parent_context.functions.copy()
    local_context.push_call(func.get('name', 'неизвестная'), func.get('args_nodes', []), args)
    for arg_name, arg_value in zip(func['args'], args):
        local_context.set(arg_name, arg_value)
    result = evaluate(func['body'].children, local_context)
    local_context.pop_call()
    return result

def evaluate_import(ast, context, current_file=None):
    debug_print("")
    debug_print("AST импортированного файла:", ast)
    debug_print("")
    
    for node in ast:
        if node.type == 'Assignment':
            var_name = node.children[0].value
            expr_value = evaluate_expression(node.children[1], context)
            if hasattr(node, 'type_hint') and node.type_hint:
                if node.type_hint.startswith('decimal:'):
                    prec = int(node.type_hint.split(':')[1])
                    getcontext().prec = prec
                    if isinstance(expr_value, (int, float, str)):
                        expr_value = Decimal(str(expr_value))
                    elif not isinstance(expr_value, Decimal):
                        raise TypeError(f"Ожидалось число для типа '{node.type_hint}', получен {type(expr_value).__name__} (строка {node.line}, столбец {node.col})")
                check_type(expr_value, node.type_hint, node)
            context.set(var_name, expr_value, node.type_hint)


        elif node.type == 'Function':
            args = [arg.value for arg in node.children[0].children]
            body = node.children[1]
            context.set_function(node.value, args, body, node.type_hint)
            debug_print(f"Зарегистрирована функция: {node.value}")
    debug_print(f"Функции в module_context после evaluate_import: {context.functions.keys()}")

def evaluate(ast, context=None, current_file=None):
    if context is None:
        context = Context()

    return_value = None
    for node in ast:

        if node.type == 'Print' or node.type == 'PrintWithSilence':
            expr_values = [evaluate_expression(child, context) for child in node.children]
            formatted_values = []
            for val in expr_values:
                if isinstance(val, bool):
                    formatted_values.append('Истина' if val else 'Ложь')
                elif isinstance(val, Decimal):
                    type_hint = None
                    if node.children and node.children[0].type == 'ID':
                        type_hint = context.type_hints.get(node.children[0].value)
                    if type_hint and type_hint.startswith('decimal:'):
                        prec = int(type_hint.split(':')[1])
                        with decimal.localcontext() as ctx:
                            ctx.prec = max(prec, len(str(val).split('.')[1]) if '.' in str(val) else 0) + 10
                            formatted_values.append(str(val.quantize(Decimal('0.' + '0' * prec))))
                    else:
                        formatted_values.append(str(val))
                else:
                    formatted_values.append(str(val))
            output = ''.join(formatted_values)
            if node.type == 'PrintWithSilence':
                print(output + '\n')
            else:
                print(output)


        elif node.type == 'Input':
            if len(node.children) == 2:
                prompt = evaluate_expression(node.children[0], context)
                var_node = node.children[1]
            else:
                prompt = ""
                var_node = node.children[0]

            var_name = var_node.value
            user_input = input(prompt)
            try:
                value = int(user_input)
            except ValueError:
                try:
                    value = float(user_input)
                except ValueError:
                    if user_input in ('истина', 'ложь'):
                        value = True if user_input == 'истина' else False
                    else:
                        value = user_input
            if hasattr(node, 'type_hint') and node.type_hint:
                if node.type_hint.startswith('decimal:'):
                    prec = int(node.type_hint.split(':')[1])
                    value = Decimal(user_input).quantize(Decimal(f'0.{"0" * prec}'))
                check_type(value, node.type_hint, node)
            context.set(var_name, value, node.type_hint)


        elif node.type == 'Assignment':
            var_name = node.children[0].value
            expr_value = evaluate_expression(node.children[1], context)
            if hasattr(node, 'type_hint') and node.type_hint:
                if node.type_hint.startswith('decimal:'):
                    prec = int(node.type_hint.split(':')[1])
                    getcontext().prec = prec
                    if isinstance(expr_value, (int, float, str)):
                        expr_value = Decimal(str(expr_value))
                    elif not isinstance(expr_value, Decimal):
                        raise TypeError(f"Ожидалось число для типа '{node.type_hint}', получен {type(expr_value).__name__} (строка {node.line}, столбец {node.col})")
                check_type(expr_value, node.type_hint, node)
            context.set(var_name, expr_value, node.type_hint)


        elif node.type == 'ArrayAssignment':
            var_name = node.children[0].value
            index = evaluate_expression(node.children[1], context)
            value = evaluate_expression(node.children[2], context)
            if var_name not in context.variables or not isinstance(context[var_name], list):
                raise ValueError(f"{var_name} не является массивом (строка {node.line}, столбец {node.col})")
            if not isinstance(index, (int, float, Decimal)) or index < 0 or index >= len(context[var_name]):
                raise ValueError(f"Недопустимый индекс {index} для массива длиной {len(context[var_name])} (строка {node.line}, столбец {node.col})")
            if var_name in context.type_hints:
                type_hint = context.type_hints[var_name]
                if type_hint.startswith('список '):
                    element_type = type_hint.split(' ')[1]
                    if element_type.startswith('decimal:'):
                        prec = int(element_type.split(':')[1])
                        getcontext().prec = prec
                        value = Decimal(str(value))
                    check_type(value, element_type, node)
            context[var_name][int(index)] = value


        elif node.type == 'While':
            condition_node = node.children[0]
            body_node = node.children[1]
            while evaluate_condition(condition_node, context):
                result = evaluate(body_node.children, context)
                if result is not None:
                    return result


        elif node.type == 'If':
            if_condition = node.children[0]
            if_body = node.children[1]
            elif_blocks = node.children[2].children
            else_body = node.children[3]
            
            if evaluate_condition(if_condition, context):
                result = evaluate(if_body.children, context)
                if result is not None:
                    return result
            else:
                executed = False
                for elif_node in elif_blocks:
                    elif_condition = elif_node.children[0]
                    elif_body = elif_node.children[1]
                    if evaluate_condition(elif_condition, context):
                        result = evaluate(elif_body.children, context)
                        if result is not None:
                            return result
                        executed = True
                        break
                if not executed and else_body.children:
                    result = evaluate(else_body.children, context)
                    if result is not None:
                        return result


        elif node.type == 'Function':
            args = [arg.value for arg in node.children[0].children]
            body = node.children[1]
            context.set_function(node.value, args, body, node.type_hint)


        elif node.type == 'Return':
            return evaluate_expression(node.children[0], context)


        elif node.type == 'Call':
            func = context.get_function(node.value)
            if not func:
                debug_print(f"Доступные функции в контексте: {context.functions.keys()}")
                raise NameError(f"Функция '{node.value}' не определена (строка {node.line}, столбец {node.col})")
            args_values = [evaluate_expression(arg, context) for arg in node.children]
            if 'builtin' in func:
                # Передаём тип аргумента для глас
                if node.value == 'глас':
                    context.push_call(node.value, node.children, args_values)
                    result = func['builtin'](*args_values, context=context, arg_type=node.children[0].type)
                    context.pop_call()
                else:
                    context.push_call(node.value, node.children, args_values)
                    result = func['builtin'](*args_values, context=context)
                    context.pop_call()
                return_value = result
            else:
                result = call_function({
                    'name': node.value,
                    'args': func['args'],
                    'body': func['body'],
                    'args_nodes': node.children
                }, args_values, context)
                return_value = result


        elif node.type == 'FixedLoop':
            iterations = node.value
            body_node = node.children[0]
            for _ in range(iterations):
                result = evaluate(body_node.children, context)
                if result is not None:
                    return result
                

        elif node.type == 'Import':
            filename = node.value
            alias = node.alias if node.alias else filename.rsplit('.', 1)[0]
            if not filename.endswith('.zg'):
                raise ValueError(f"Импортируемый файл должен иметь расширение .zg, получено '{filename}' (строка {node.line}, столбец {node.col})")

            file_to_import = filename
            if current_file:
                current_dir = os.path.dirname(os.path.abspath(current_file))
                possible_path = os.path.join(current_dir, filename)
                if os.path.exists(possible_path):
                    file_to_import = possible_path
                else:
                    root_dir = os.path.dirname(current_dir)
                    libs_path = os.path.join(root_dir, 'libs', filename)
                    if os.path.exists(libs_path):
                        file_to_import = libs_path

            try:
                with open(file_to_import, 'r', encoding='utf-8') as f:
                    imported_code = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"Файл '{filename}' не найден (строка {node.line}, столбец {node.col})")
            except Exception as e:
                raise RuntimeError(f"Ошибка при чтении файла '{filename}': {str(e)} (строка {node.line}, столбец {node.col})")

            imported_tokens = tokenize(imported_code)
            imported_ast = parse(imported_tokens, imported_code)

            module_context = Context(parent=context)
            evaluate_import(imported_ast, module_context, current_file=file_to_import)

            debug_print(f"Функции в module_context перед переносом: {module_context.functions.keys()}")
            for func_name, func_def in module_context.functions.items():
                if func_name in context.functions:
                    raise NameError(f"Конфликт имён: функция '{func_name}' уже определена (строка {node.line}, столбец {node.col})")
                context.set_function(func_name, func_def['args'], func_def['body'], func_def['return_type'])
                debug_print(f"Перенесена функция в context: {func_name}")
            debug_print(f"Функции в context после импорта: {context.functions.keys()}")

            if node.alias is None:
                for var_name, var_value in module_context.variables.items():
                    if var_name in context.variables:
                        raise NameError(f"Конфликт имён: переменная '{var_name}' уже определена в текущем контексте (строка {node.line}, столбец {node.col})")
                    context.set(var_name, var_value, module_context.type_hints.get(var_name))
            else:
                context.set(alias, module_context.variables)

    return return_value