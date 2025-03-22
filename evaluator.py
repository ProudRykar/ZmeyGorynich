import math

class Context:
    def __init__(self):
        self.variables = {}  # Хранит значения переменных
        self.type_hints = {}  # Хранит типы переменных

    def get(self, key, default=None):
        return self.variables.get(key, default)

    def set(self, key, value, type_hint=None):
        self.variables[key] = value
        if type_hint:
            self.type_hints[key] = type_hint

    def __setitem__(self, key, value):
        self.variables[key] = value

    def __getitem__(self, key):
        return self.variables[key]

def evaluate_expression(node, context):
    if node.type == 'строченька':
        return node.value.strip('"')
    
    elif node.type == 'число':
        # node.value — это строка, например "5" или "5.5"
        return float(node.value) if '.' in node.value else int(node.value)
    
    elif node.type == 'ID':
        if node.value not in context.variables:
            raise NameError(f"Переменная '{node.value}' не определена (строка {node.line}, столбец {node.col})")
        return context[node.value]
    
    elif node.type == 'Array':
        return [evaluate_expression(child, context) for child in node.children]
        
    elif node.type == 'ArrayAccess':
        array = evaluate_expression(node.children[0], context)
        index = evaluate_expression(node.children[1], context)
        if not isinstance(array, list):
            raise ValueError(f"Индексация возможна только для массивов, а не для {type(array).__name__} (строка {node.line}, столбец {node.col})")
        if not isinstance(index, (int, float)) or index < 0 or index >= len(array):
            raise ValueError(f"Недопустимый индекс {index} для массива длиной {len(array)} (строка {node.line}, столбец {node.col})")
        return array[int(index)]
    
    elif node.type == 'ArrayAssignment':
        raise ValueError("ArrayAssignment не является выражением и не может быть использовано в evaluate_expression")
    
    elif node.type == 'ArrayCreate':
        size = evaluate_expression(node.children[0], context)
        value = evaluate_expression(node.children[1], context)
        if not isinstance(size, (int, float)) or size < 0:
            raise ValueError(f"Размер массива должен быть неотрицательным числом, а не {size} (строка {node.line}, столбец {node.col})")
        array = [value] * int(size)
        # Проверка типа элементов массива, если он указан
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
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            raise ValueError(f"Нельзя сложить {type(left).__name__} и {type(right).__name__} с помощью '+' (строка {node.line}, столбец {node.col})")
        
        if not (isinstance(left, (int, float)) and isinstance(right, (int, float))):
            raise ValueError(f"Операция '{node.op}' поддерживается только для чисел, а не для {type(left).__name__} и {type(right).__name__} (строка {node.line}, столбец {node.col})")
        
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
        if not isinstance(value, (int, float)):
            raise ValueError(f"Корень можно извлечь только из числа, а не из {type(value).__name__} (строка {node.line}, столбец {node.col})")
        if value < 0:
            raise ValueError(f"Корень нельзя извлечь из отрицательного числа {value} (строка {node.line}, столбец {node.col})")
        root_value = math.sqrt(value)
        if root_value.is_integer():
            return int(root_value)
        return root_value

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
        }
        operation = ops.get(node.op)
        if operation:
            return operation(left, right)
        raise ValueError(f"Неизвестная операция условия: {node.op} (строка {node.line}, столбец {node.col})")
    return False

def check_type(value, type_hint, node):
    if type_hint == 'строченька':
        if not isinstance(value, str):
            raise TypeError(f"Значение должно быть строченькой, а не {type(value).__name__} (строка {node.line}, столбец {node.col})")
    elif type_hint.startswith('число'):
        if not isinstance(value, (int, float)):
            raise TypeError(f"Значение должно быть числом, а не {type(value).__name__} (строка {node.line}, столбец {node.col})")
        # Проверяем подтип числа, если он указан
        if ':' in type_hint:
            subtype = type_hint.split(':')[1]
            if subtype == 'int' and not isinstance(value, int):
                raise TypeError(f"Значение должно быть целым числом (int), а не {type(value).__name__} (строка {node.line}, столбец {node.col})")
            elif subtype == 'float' and not isinstance(value, float):
                raise TypeError(f"Значение должно быть числом с плавающей точкой (float), а не {type(value).__name__} (строка {node.line}, столбец {node.col})")
    elif type_hint.startswith('список '):
        if not isinstance(value, list):
            raise TypeError(f"Значение должно быть списком, а не {type(value).__name__} (строка {node.line}, столбец {node.col})")
        element_type = type_hint.split(' ')[1]
        for item in value:
            check_type(item, element_type, node)
    return True

def evaluate(ast, context=None):
    if context is None:
        context = Context()

    for node in ast:
        if node.type == 'Print':
            expr_values = [evaluate_expression(child, context) for child in node.children]
            result = ''.join(str(val) for val in expr_values)
            print(result)

        elif node.type == 'Input':
            var_name = node.children[0].value
            user_input = input("")
            try:
                value = int(user_input)
            except ValueError:
                try:
                    value = float(user_input)
                except ValueError:
                    value = user_input
            # Проверка типа, если он указан
            if hasattr(node, 'type_hint') and node.type_hint:
                check_type(value, node.type_hint, node)
            context.set(var_name, value, node.type_hint)

        elif node.type == 'Assignment':
            var_name = node.children[0].value
            expr_value = evaluate_expression(node.children[1], context)
            # Проверка типа, если он указан
            if hasattr(node, 'type_hint') and node.type_hint:
                check_type(expr_value, node.type_hint, node)
            context.set(var_name, expr_value, node.type_hint)

        elif node.type == 'ArrayAssignment':
            var_name = node.children[0].value
            index = evaluate_expression(node.children[1], context)
            value = evaluate_expression(node.children[2], context)
            if var_name not in context.variables or not isinstance(context[var_name], list):
                raise ValueError(f"{var_name} не является массивом (строка {node.line}, столбец {node.col})")
            if not isinstance(index, (int, float)) or index < 0 or index >= len(context[var_name]):
                raise ValueError(f"Недопустимый индекс {index} для массива длиной {len(context[var_name])} (строка {node.line}, столбец {node.col})")
            # Проверка типа элемента массива, если массив типизирован
            if var_name in context.type_hints:
                type_hint = context.type_hints[var_name]
                if type_hint.startswith('список '):
                    element_type = type_hint.split(' ')[1]
                    check_type(value, element_type, node)
            context[var_name][int(index)] = value

        elif node.type == 'While':
            condition_node = node.children[0]
            body_node = node.children[1]
            while evaluate_condition(condition_node, context):
                evaluate(body_node.children, context)

        elif node.type == 'If':
            if_condition = node.children[0]
            if_body = node.children[1]
            elif_blocks = node.children[2].children
            else_body = node.children[3]
            
            if evaluate_condition(if_condition, context):
                evaluate(if_body.children, context)
            else:
                executed = False
                for elif_node in elif_blocks:
                    elif_condition = elif_node.children[0]
                    elif_body = elif_node.children[1]
                    if evaluate_condition(elif_condition, context):
                        evaluate(elif_body.children, context)
                        executed = True
                        break
                if not executed and else_body.children:
                    evaluate(else_body.children, context)