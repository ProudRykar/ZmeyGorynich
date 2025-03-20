import math


def evaluate(ast, context):
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
            context[var_name] = value

        elif node.type == 'Assignment':
            var_name = node.children[0].value
            expr_value = evaluate_expression(node.children[1], context)
            context[var_name] = expr_value

        elif node.type == 'ArrayAssignment':
            var_name = node.children[0].value
            index = evaluate_expression(node.children[1], context)
            value = evaluate_expression(node.children[2], context)
            if var_name not in context or not isinstance(context[var_name], list):
                raise ValueError(f"{var_name} не является массивом")
            if not isinstance(index, (int, float)) or index < 0 or index >= len(context[var_name]):
                raise ValueError(f"Недопустимый индекс {index} для массива длиной {len(context[var_name])}")
            context[var_name][int(index)] = value

        elif node.type == 'While':
            condition_node = node.children[0]
            body_node = node.children[1]
            while evaluate_condition(condition_node, context):
                evaluate(body_node.children, context)

def evaluate_expression(node, context):
    if node.type == 'строченька':
        return node.value.strip('"')
    
    elif node.type == 'число':
        return node.value
    
    elif node.type == 'ID':
        return context.get(node.value, node.value)
    
    elif node.type == 'Array':
        return [evaluate_expression(child, context) for child in node.children]
        
    elif node.type == 'ArrayAccess':
        array = evaluate_expression(node.children[0], context)
        index = evaluate_expression(node.children[1], context)
        if not isinstance(array, list):
            raise ValueError(f"Индексация возможна только для массивов, а не для {type(array)}")
        if not isinstance(index, (int, float)) or index < 0 or index >= len(array):
            raise ValueError(f"Недопустимый индекс {index} для массива длиной {len(array)}")
        return array[int(index)]
    
    elif node.type == 'ArrayAssignment':
        raise ValueError("ArrayAssignment не является выражением и не может быть использовано в evaluate_expression")
    
    elif node.type == 'ArrayCreate':
        size = evaluate_expression(node.children[0], context)
        value = evaluate_expression(node.children[1], context)
        if not isinstance(size, (int, float)) or size < 0:
            raise ValueError(f"Размер массива должен быть неотрицательным числом, а не {size}")
        return [value] * int(size)

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
            raise ValueError(f"Нельзя сложить {type(left)} и {type(right)} с помощью '+'")
        
        if not (isinstance(left, (int, float)) and isinstance(right, (int, float))):
            raise ValueError(f"Операция '{node.op}' поддерживается только для чисел, а не для {type(left)} и {type(right)}")
        
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
            raise ValueError("Корень можно извлечь только из числа")
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
            '=': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
        }
        operation = ops.get(node.op)
        if operation:
            return operation(left, right)
        raise ValueError(f"Неизвестная операция условия: {node.op}")
    return False