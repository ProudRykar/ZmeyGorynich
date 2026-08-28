"""Поиск справки (hover/calltip) по имени идентификатора."""
from ide.analysis.completions import BUILTIN_DOCS, TYPES
from ide.lang_core import map_type_hint_to_display_name


def describe(name, symbols):
    """Вернуть строку-описание для имени или None."""
    # встроенные
    if name in BUILTIN_DOCS:
        doc, sig = BUILTIN_DOCS[name]
        return f"{sig}\n\n{doc}"

    # пользовательские символы
    sym = symbols.lookup(name) if symbols is not None else None
    if sym is not None:
        if sym.kind == "function":
            args = ", ".join(
                f"{a[0]} быти {map_type_hint_to_display_name(a[1], None)}"
                if a[1] else a[0]
                for a in sym.args
            )
            ret = map_type_hint_to_display_name(sym.ret, None) if sym.ret else "?"
            return f"сотвори {sym.name}({args}) изречет {ret}"
        else:
            hint = map_type_hint_to_display_name(sym.type_hint, None) if sym.type_hint else "?"
            return f"переменная: {sym.name} быти {hint}"

    # типы
    if name in TYPES:
        return f"тип: {name}"

    return None
