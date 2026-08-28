from config import debug_print
from zg_builtins import builtins


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
