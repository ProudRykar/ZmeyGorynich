from parser import parse
import decimal
import math
from decimal import Decimal, getcontext
import os
from lexer import tokenize

getcontext().prec = 100

class Context:
    def __init__(self, parent=None):
        self.variables = {}
        self.type_hints = {}
        self.functions = {
            'созвать_дружину': {
                'args': ['size', 'value'],
                'body': None,
                'return_type': 'list:число:int',
                'builtin': lambda size, value: [value] * int(size)
            }
        }
        self.parent = parent

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

    def get_function(self, name):
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.get_function(name)
        return None

    def __setitem__(self, key, value):
        self.variables[key] = value

    def __getitem__(self, key):
        return self.variables[key]

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
        return Decimal(value) if '.' in value else int(value)
    
    elif node.type == 'двосуть':
        return node.value
    
    elif node.type == 'ID':
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
            return func['builtin'](*args)
        else:
            return call_function(func, args, context)
    raise ValueError(f"Неизвестный тип выражения: {node.type}")

    return None

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
        raise ValueError(f"Функция ожидает {len(func['args'])} аргументов, получено {len(args)}")
    local_context = Context(parent=parent_context)
    for arg_name, arg_value in zip(func['args'], args):
        local_context.set(arg_name, arg_value)
    return evaluate(func['body'].children, local_context)

def evaluate(ast, context=None, current_file=None):
    if context is None:
        context = Context()

    return_value = None
    for node in ast:
        if node.type == 'Print':
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
            print(''.join(formatted_values))

        elif node.type == 'Input':
            var_name = node.children[0].value
            user_input = input("")
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
                raise NameError(f"Функция '{node.value}' не определена (строка {node.line}, столбец {node.col})")
            args = [evaluate_expression(arg, context) for arg in node.children]
            if 'builtin' in func:
                func['builtin'](*args)
            else:
                call_function(func, args, context)

        elif node.type == 'FixedLoop':
            iterations = node.value
            body_node = node.children[0]
            for _ in range(iterations):
                result = evaluate(body_node.children, context)
                if result is not None:
                    return result
                
        elif node.type == 'Import':
            filename = node.value
            if not filename.endswith('.zg'):
                raise ValueError(f"Импортируемый файл должен иметь расширение .zg, получено '{filename}' (строка {node.line}, столбец {node.col})")

            file_to_import = filename
            if current_file:
                current_dir = os.path.dirname(os.path.abspath(current_file))
                possible_path = os.path.join(current_dir, filename)
                if os.path.exists(possible_path):
                    file_to_import = possible_path

            try:
                with open(file_to_import, 'r', encoding='utf-8') as f:
                    imported_code = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"Файл '{filename}' не найден (строка {node.line}, столбец {node.col})")
            except Exception as e:
                raise RuntimeError(f"Ошибка при чтении файла '{filename}': {str(e)} (строка {node.line}, столбец {node.col})")

            imported_tokens = tokenize(imported_code)
            imported_ast = parse(imported_tokens, imported_code)

            evaluate(imported_ast, context, current_file=file_to_import)

    return return_value