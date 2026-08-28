"""Таблица символов: функции и переменные, собранные из AST."""


class Symbol:
    def __init__(self, kind, name, line, col, type_hint=None, args=None, ret=None, scope="global"):
        self.kind = kind          # 'function' | 'variable'
        self.name = name
        self.line = line
        self.col = col
        self.type_hint = type_hint
        self.args = args or []    # для функций: [(arg_name, type_hint), ...]
        self.ret = ret            # для функций: тип возврата
        self.scope = scope

    def signature(self):
        if self.kind == "function":
            args = ", ".join(a[0] for a in self.args)
            ret = self.ret or ""
            return f"сотвори {self.name}({args}) изречет {ret}"
        hint = self.type_hint or ""
        return f"{self.name} быти {hint}"


class SymbolTable:
    def __init__(self):
        self.functions = {}   # name -> Symbol
        self.variables = {}  # name -> Symbol

    def add_function(self, sym):
        self.functions[sym.name] = sym

    def add_variable(self, sym):
        # переменная: оставляем первое определение (для hover/автодополнения)
        if sym.name not in self.variables:
            self.variables[sym.name] = sym

    def lookup(self, name):
        if name in self.functions:
            return self.functions[name]
        if name in self.variables:
            return self.variables[name]
        return None
