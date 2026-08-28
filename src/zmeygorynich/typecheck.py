from decimal import Decimal, getcontext


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
