import decimal
import math
from decimal import Decimal, getcontext
import os
from lexer import tokenize
from parser import parse
from colored_text import Color
from config import debug_print
from context import Context
from typecheck import (get_type_name, map_type_hint_to_display_name,
                       stringify_value, check_type)


def normalize_operator(op: str) -> str:
    """
    Нормализует оператор из AST в унифицированную форму, понятную интерпретатору.
    Убирает лишние пробелы/двоеточия, приводит к нижнему регистру, заменяет букву 'ё' на 'е'
    и поддерживает большое количество русских синонимов.
    """
    if not isinstance(op, str):
        return op

    o = op.strip().lower()
    if o.endswith(':'):
        o = o[:-1].strip()
    o = o.replace('ё', 'е')

    o = ' '.join(o.split())

    mapping = {
        'прибави': '+', 'прибавить': '+', 'плюс': '+',
        'отними': '-', 'вычти': '-', 'минус': '-',
        'умножи на': '*', 'умножить на': '*', 'умножи': '*',
        'раздели на': '/', 'разделить на': '/', 'дели на': '/',
        'остаток от': '%', 'мод': '%',
        'возвысить в': '**', 'возвысить': '**', 'возвести в': '**', 'в степенне': '**',

        'превосходит': '>', 'превышает': '>', 'больше': '>',
        'уступает': '<', 'меньше': '<', 'меньше чем': '<',
        'ровно': '==', 'равно': '==', 'есть': '==', 'равно ли': '==',
        'не равно': '!=', 'неравно': '!=', 'не равно ли': '!=', 'не есть': '!=',
        'ровно либо превосходит': '>=', 'ровно или превосходит': '>=', 'больше или равно': '>=',
        'ровно либо уступает': '<=', 'ровно или уступает': '<=', 'меньше или равно': '<=',

        'и': 'and', 'или': 'or', 'не': 'not',
        'and': 'and', 'or': 'or', 'not': 'not',
        '>': '>', '<': '<', '>=': '>=', '<=': '<=', '==': '==', '!=': '!=',
    }

    return mapping.get(o, o)


def evaluate_expression(node, context):
    if node.type == 'строченька':
        return node.value.strip('"')

    elif node.type == 'число':
        value = node.value
        type_hint = getattr(node, 'type_hint', None)
        if type_hint:
            if type_hint.startswith('decimal:'):
                prec = int(type_hint.split(':')[1])
                getcontext().prec = prec
                return Decimal(value)
            elif type_hint == 'число:int':
                return int(value)
            elif type_hint == 'число:float':
                return float(value)

        if context.call_stack and context.call_stack[-1]['args_nodes']:
            arg_name = context.get_call_arg_name()
            if arg_name in context.type_hints:
                type_hint = context.type_hints[arg_name]
                if type_hint.startswith('decimal:'):
                    prec = int(type_hint.split(':')[1])
                    getcontext().prec = prec
                    return Decimal(value)
                elif type_hint == 'число:int':
                    return int(value)
                elif type_hint == 'число:float':
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
        op = normalize_operator(node.op)
        left = evaluate_expression(node.children[0], context)
        right = evaluate_expression(node.children[1], context)

        comparison_ops = {
            '<': lambda x, y: x < y,
            '>': lambda x, y: x > y,
            '<=': lambda x, y: x <= y,
            '>=': lambda x, y: x >= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
        }

        if op in comparison_ops:
            return comparison_ops[op](left, right)

        if op in ('and', 'or'):
            if op == 'and':
                return bool(left) and bool(right)
            return bool(left) or bool(right)


        if op == '+':
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
            raise ValueError(f"Операция '{op}' поддерживается только для чисел, а не для {type(left).__name__} и {type(right).__name__} (строка {node.line}, столбец {node.col})")

        if isinstance(left, Decimal) or isinstance(right, Decimal):
            left = Decimal(str(left))
            right = Decimal(str(right))

        # ДО блока ops
        ops = {
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '%': lambda x, y: x % y,
            '**': lambda x, y: x ** y,
        }
        operation = ops.get(op)
        if operation:
            return operation(left, right)
        return None

    elif node.type == 'UnaryOp':
        op = normalize_operator(node.op)
        operand = evaluate_expression(node.children[0], context)
        if op == 'not':
            return not bool(operand)
        raise ValueError(f"Неизвестная унарная операция: {op} (строка {node.line}, столбец {node.col})")

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
    """Вычисляет условие (сравнения, логические И/ИЛИ/НЕ)."""
    return evaluate_expression(node, context)


def call_function(func, args, parent_context):
    if len(args) != len(func['args']):
        raise ValueError(f"Функция '{func.get('name', 'неизвестная')}' ожидает {len(func['args'])} аргументов, получено {len(args)}")
    local_context = Context(parent=parent_context)
    local_context.functions = parent_context.functions.copy()
    local_context.push_call(func.get('name', 'неизвестная'), func.get('args_nodes', []), args)

    debug_print(f"Аргументы функции {func.get('name')}: {[(arg_name, type(arg_value), arg_value) for arg_name, arg_value in zip(func['args'], args)]}")

    for arg_name, arg_value, arg_node in zip(func['args'], args, func.get('args_nodes', [])):
        type_hint = None
        for arg in func['body'].children[0].children:
            if arg.value == arg_name:
                type_hint = arg.type_hint
                break
        if type_hint:
            if type_hint.startswith('decimal:'):
                prec = int(type_hint.split(':')[1])
                getcontext().prec = prec
                if not isinstance(arg_value, Decimal):
                    arg_value = Decimal(str(arg_value))
            elif type_hint == 'число:int':
                arg_value = int(arg_value)
            elif type_hint == 'число:float':
                arg_value = float(arg_value)
            elif type_hint == 'строченька':
                arg_value = str(arg_value)
            elif type_hint == 'двосуть':
                arg_value = bool(arg_value)
            check_type(arg_value, type_hint, arg_node)
        local_context.set(arg_name, arg_value, type_hint)

    result = evaluate(func['body'].children, local_context)
    local_context.pop_call()

    return_type = func.get('return_type')
    if return_type and result is not None:
        if return_type.startswith('decimal:'):
            prec = int(return_type.split(':')[1])
            getcontext().prec = prec
            if not isinstance(result, Decimal):
                result = Decimal(str(result))
        elif return_type == 'число:int':
            result = int(result)
        elif return_type == 'число:float':
            result = float(result)
        elif return_type == 'строченька':
            result = str(result)
        elif return_type == 'двосуть':
            result = bool(result)
        check_type(result, return_type, None)

    debug_print(f"Результат функции {func.get('name')}: {type(result)}, {result}")

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


class Evaluator:
    """Обход AST и выполнение узлов. Каждый тип узла обрабатывается
    отдельным методом _eval_<Тип>."""

    def __init__(self, context, current_file=None):
        self.context = context
        self.current_file = current_file

    def evaluate(self, ast):
        self.return_value = None
        for node in ast:
            handler = getattr(self, '_eval_' + node.type, None)
            if handler is None:
                continue
            ret = handler(node)
            if ret is not None:
                return ret
        return self.return_value

    def _eval_Print(self, node):
        expr_values = [evaluate_expression(child, self.context) for child in node.children]
        formatted_values = []
        for val in expr_values:
            if isinstance(val, bool):
                formatted_values.append('Истина' if val else 'Ложь')
            elif isinstance(val, Decimal):
                type_hint = None
                if node.children and node.children[0].type == 'ID':
                    type_hint = self.context.type_hints.get(node.children[0].value)
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
        return None

    def _eval_Input(self, node):
        if len(node.children) == 2:
            prompt = evaluate_expression(node.children[0], self.context)
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
        self.context.set(var_name, value, node.type_hint)
        return None

    def _eval_Assignment(self, node):
        var_name = node.children[0].value
        expr_value = evaluate_expression(node.children[1], self.context)
        if hasattr(node, 'type_hint') and node.type_hint:
            if node.type_hint.startswith('decimal:'):
                prec = int(node.type_hint.split(':')[1])
                getcontext().prec = prec
                if isinstance(expr_value, (int, float, str)):
                    expr_value = Decimal(str(expr_value))
                elif not isinstance(expr_value, Decimal):
                    raise TypeError(f"Ожидалось число для типа '{node.type_hint}', получен {type(expr_value).__name__} (строка {node.line}, столбец {node.col})")
            check_type(expr_value, node.type_hint, node)
        self.context.set(var_name, expr_value, node.type_hint)
        return None

    def _eval_ArrayAssignment(self, node):
        var_name = node.children[0].value
        index = evaluate_expression(node.children[1], self.context)
        value = evaluate_expression(node.children[2], self.context)
        if var_name not in self.context.variables or not isinstance(self.context[var_name], list):
            raise ValueError(f"{var_name} не является массивом (строка {node.line}, столбец {node.col})")
        if not isinstance(index, (int, float, Decimal)) or index < 0 or index >= len(self.context[var_name]):
            raise ValueError(f"Недопустимый индекс {index} для массива длиной {len(self.context[var_name])} (строка {node.line}, столбец {node.col})")
        if var_name in self.context.type_hints:
            type_hint = self.context.type_hints[var_name]
            if type_hint.startswith('список '):
                element_type = type_hint.split(' ')[1]
                if element_type.startswith('decimal:'):
                    prec = int(element_type.split(':')[1])
                    getcontext().prec = prec
                    value = Decimal(str(value))
                check_type(value, element_type, node)
        self.context[var_name][int(index)] = value
        return None

    def _eval_While(self, node):
        condition_node = node.children[0]
        body_node = node.children[1]
        while evaluate_condition(condition_node, self.context):
            result = self.evaluate(body_node.children)
            if result is not None:
                return result
        return None

    def _eval_If(self, node):
        if_condition = node.children[0]
        if_body = node.children[1]
        elif_blocks = node.children[2].children
        else_body = node.children[3]

        if evaluate_condition(if_condition, self.context):
            result = self.evaluate(if_body.children)
            if result is not None:
                return result
        else:
            executed = False
            for elif_node in elif_blocks:
                elif_condition = elif_node.children[0]
                elif_body = elif_node.children[1]
                if evaluate_condition(elif_condition, self.context):
                    result = self.evaluate(elif_body.children)
                    if result is not None:
                        return result
                    executed = True
                    break
            if not executed and else_body.children:
                result = self.evaluate(else_body.children)
                if result is not None:
                    return result
        return None

    def _eval_Function(self, node):
        args = [arg.value for arg in node.children[0].children]
        body = node.children[1]
        self.context.set_function(node.value, args, body, node.type_hint)
        return None

    def _eval_Return(self, node):
        return evaluate_expression(node.children[0], self.context)

    def _eval_Call(self, node):
        func = self.context.get_function(node.value)
        if not func:
            debug_print(f"Доступные функции в контексте: {self.context.functions.keys()}")
            raise NameError(f"Функция '{node.value}' не определена (строка {node.line}, столбец {node.col})")
        args_values = [evaluate_expression(arg, self.context) for arg in node.children]
        if 'builtin' in func:
            if node.value == 'глас':
                self.context.push_call(node.value, node.children, args_values)
                result = func['builtin'](*args_values, context=self.context, arg_type=node.children[0].type)
                self.context.pop_call()
            else:
                self.context.push_call(node.value, node.children, args_values)
                result = func['builtin'](*args_values, context=self.context)
                self.context.pop_call()
            self.return_value = result
        else:
            node.type_hint = func.get('return_type')  # Assign return type to node
            result = call_function({
                'name': node.value,
                'args': func['args'],
                'body': func['body'],
                'args_nodes': node.children
            }, args_values, self.context)
            check_type(result, node.type_hint, node)
            self.return_value = result
        return None

    def _eval_FixedLoop(self, node):
        iterations = node.value
        body_node = node.children[0]
        for _ in range(iterations):
            result = self.evaluate(body_node.children)
            if result is not None:
                return result
        return None

    def _eval_Import(self, node):
        filename = node.value
        alias = node.alias if node.alias else filename.rsplit('.', 1)[0]
        if not filename.endswith('.zg'):
            raise ValueError(f"Импортируемый файл должен иметь расширение .zg, получено '{filename}' (строка {node.line}, столбец {node.col})")

        file_to_import = filename
        if self.current_file:
            current_dir = os.path.dirname(os.path.abspath(self.current_file))
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

        module_context = Context(parent=self.context)
        evaluate_import(imported_ast, module_context, current_file=file_to_import)

        debug_print(f"Функции в module_context перед переносом: {module_context.functions.keys()}")
        for func_name, func_def in module_context.functions.items():
            if func_name in self.context.functions:
                raise NameError(f"Конфликт имён: функция '{func_name}' уже определена (строка {node.line}, столбец {node.col})")
            self.context.set_function(func_name, func_def['args'], func_def['body'], func_def['return_type'])
            debug_print(f"Перенесена функция в context: {func_name}")
        debug_print(f"Функции в context после импорта: {self.context.functions.keys()}")

        if node.alias is None:
            for var_name, var_value in module_context.variables.items():
                if var_name in self.context.variables:
                    raise NameError(f"Конфликт имён: переменная '{var_name}' уже определена в текущем контексте (строка {node.line}, столбец {node.col})")
                self.context.set(var_name, var_value, module_context.type_hints.get(var_name))
        else:
            self.context.set(alias, module_context.variables)
        return None


def evaluate(ast, context=None, current_file=None):
    """Выполнить AST в заданном контексте."""
    if context is None:
        context = Context()
    return Evaluator(context, current_file).evaluate(ast)
