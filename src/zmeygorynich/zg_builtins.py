from colored_text import Color
from typecheck import (map_type_hint_to_display_name, stringify_value,
                       get_type_name)


def _glas(value, context=None, arg_type=None):
    """Встроенная функция 'глас' — печатает значение вместе с его типом и аргументами."""
    from evaluator import evaluate_expression

    name = context.get_call_arg_name()
    is_function_call = (arg_type == 'Call')
    func_name = context.call_stack[-1]['args_nodes'][0].value if is_function_call else name
    func_def = context.get_function(func_name) if is_function_call else None
    return_type_hint = func_def.get('return_type') if func_def and is_function_call else None

    if is_function_call and return_type_hint:
        type_name = map_type_hint_to_display_name(return_type_hint, value)
    elif context and name in context.type_hints and not is_function_call:
        type_name = map_type_hint_to_display_name(context.type_hints.get(name, None), value)
    else:
        type_name = get_type_name(value)

    if is_function_call:
        args_nodes = context.call_stack[-1]['args_nodes'][0].children
        args_values = [evaluate_expression(arg_node, context) for arg_node in args_nodes]
    else:
        args_nodes = []
        args_values = []

    args_with_types = []
    if is_function_call:
        for i, (arg_node, arg_value) in enumerate(zip(args_nodes, args_values)):
            if arg_node.type == 'ID' and arg_node.value in context.type_hints:
                arg_type_name = map_type_hint_to_display_name(
                    context.type_hints.get(arg_node.value, None), arg_value)
            elif is_function_call and func_name + ':' + str(i) in context.type_hints:
                arg_type_name = map_type_hint_to_display_name(
                    context.type_hints.get(func_name + ':' + str(i), None), arg_value)
            else:
                arg_type_name = get_type_name(arg_value)
            arg_label = arg_node.value if arg_node.type == 'ID' else stringify_value(arg_value)
            args_with_types.append((arg_label, arg_value, arg_type_name))

    all_same_type = len(set(arg[2] for arg in args_with_types)) == 1 if args_with_types else False

    if is_function_call:
        if all_same_type and args_with_types:
            args_str = (f"{Color.BLUE.value}{', '.join(stringify_value(arg[1]) for arg in args_with_types)}{Color.RESET_ALL.value} "
                        f"быти {Color.YELLOW.value}{args_with_types[0][2]}")
        else:
            args_str = ', '.join(
                f"{Color.BLUE.value}{stringify_value(arg[1])}{Color.RESET_ALL.value} быти {Color.YELLOW.value}{arg[2]}"
                for arg in args_with_types)
    else:
        args_str = (f"{Color.BLUE.value}{stringify_value(value)}{Color.RESET_ALL.value} "
                    f"быти {Color.YELLOW.value}{type_name}{Color.RESET_ALL.value}")

    call_name = (f"{func_name}({', '.join(stringify_value(arg) for arg in args_values)})"
                 if is_function_call else name)

    result = (f"{Color.CYAN.value}ᚨᛇᛟ: "
              f"{Color.MAGENTA.value if is_function_call else Color.GREEN.value}{call_name}{Color.RESET_ALL.value} -> "
              f"{Color.GREEN.value}{args_str}{Color.RESET_ALL.value}")
    if is_function_call:
        result += (f" -> {Color.BLUE.value}{stringify_value(value)}{Color.RESET_ALL.value} "
                   f"быти {Color.YELLOW.value}{type_name}{Color.RESET_ALL.value}")

    print(result)
    return result


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
        'builtin': _glas
    },
    'молвить': {
        'builtin': lambda value, context=None: print(value)
    }
}
