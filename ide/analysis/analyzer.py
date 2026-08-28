"""Анализ исходного кода .zg: диагностика и таблица символов.

Использует ядро языка (lexer/parser) напрямую. Диагностика собирается из:
  * ошибок синтаксиса (SyntaxError от tokenize/parse) — с привязкой к строке/столбцу;
  * лёгких статических проверок по AST (повтор функции, число аргументов вызова).
"""
import re

from ide.lang_core import tokenize, parse_with_errors
from ide.analysis.symbols import Symbol, SymbolTable

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text):
    return _ANSI_RE.sub("", text)


class Diagnostic:
    def __init__(self, line, col, message, severity="error"):
        self.line = line      # 1-based
        self.col = col        # 1-based
        self.message = message
        self.severity = severity  # 'error' | 'warning'

    def __repr__(self):
        kind = "Ошибка" if self.severity == "error" else "Предупреждение"
        return f"{kind} ({self.line}:{self.col}): {self.message}"


def _loc_from_exc(exc, code):
    """Извлечь (line, col) из SyntaxError, если доступно."""
    line = getattr(exc, "lineno", None)
    col = getattr(exc, "offset", None)
    if line:
        return line, (col or 1)
    msg = str(exc)
    # форматы из ядра: "(строка N)" или "(строка N, столбец M)"
    m = re.search(r"строка\s+(\d+)(?:\s*,\s*столбец\s+(\d+))?", msg)
    if m:
        return int(m.group(1)), int(m.group(2)) if m.group(2) else 1
    return 1, 1


def analyze(code):
    """Вернуть (diagnostics, symbols, ast). ast может быть None при фатальной ошибке."""
    diags = []
    symbols = SymbolTable()

    try:
        tokens = tokenize(code)
    except SyntaxError as exc:
        line, col = _loc_from_exc(exc, code)
        diags.append(Diagnostic(line, col, strip_ansi(str(exc)), "error"))
        return diags, symbols, None

    if not tokens:
        return diags, symbols, []

    try:
        ast, parse_errors = parse_with_errors(tokens, code)
    except SyntaxError as exc:
        line, col = _loc_from_exc(exc, code)
        diags.append(Diagnostic(line, col, strip_ansi(str(exc)), "error"))
        return diags, symbols, None
    except Exception as exc:  # noqa: BLE001
        # на незавершённый при наборе ввод парсер может упасть не как SyntaxError —
        # не крашим IDE, а показываем общую диагностику
        diags.append(Diagnostic(1, 1, strip_ansi(str(exc)), "error"))
        return diags, symbols, None

    for exc in parse_errors:
        line, col = _loc_from_exc(exc, code)
        diags.append(Diagnostic(line, col, strip_ansi(str(exc)), "error"))

    _collect_symbols(ast, symbols, diags)
    return diags, symbols, ast


def _walk(node, visit):
    if node is None:
        return
    visit(node)
    children = getattr(node, "children", None) or []
    for child in children:
        _walk(child, visit)


def _collect_symbols(ast, symbols, diags):
    functions = {}

    def visit(node):
        t = node.type

        if t == "Function":
            name = node.value
            args = []
            if node.children and node.children[0].type == "Args":
                for a in node.children[0].children:
                    args.append((a.value, getattr(a, "type_hint", None)))
            ret = node.type_hint
            sym = Symbol("function", name, node.line, node.col,
                         args=args, ret=ret, scope="global")
            if name in functions:
                diags.append(Diagnostic(
                    node.line, node.col,
                    f"Повторное определение функции '{name}'", "error"))
            functions[name] = sym
            symbols.add_function(sym)

        elif t == "Assignment":
            var = node.children[0] if node.children else None
            if var is not None and var.type == "ID":
                symbols.add_variable(Symbol(
                    "variable", var.value, node.line, node.col,
                    type_hint=node.type_hint, scope="global"))

        elif t == "ArrayAssignment":
            var = node.children[0] if node.children else None
            if var is not None and var.type == "ID":
                symbols.add_variable(Symbol(
                    "variable", var.value, node.line, node.col,
                    type_hint=node.type_hint, scope="global"))

        elif t == "Call":
            name = node.value
            if name in functions:
                expected = len(functions[name].args)
                got = len(node.children or [])
                if expected != got:
                    diags.append(Diagnostic(
                        node.line, node.col,
                        f"Функция '{name}' ожидает {expected} аргумент(ов), получено {got}",
                        "warning"))

    for top in ast:
        _walk(top, visit)
