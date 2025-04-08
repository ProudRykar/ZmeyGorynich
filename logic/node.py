class Node:
    def __init__(self, type, value=None, children=None, op=None, type_hint=None, line=None, col=None, alias=None):
        self.type = type
        self.value = value
        self.children = children if children is not None else []
        self.op = op
        self.type_hint = type_hint
        self.line = line
        self.col = col
        self.alias = alias

    def __repr__(self):
        op_str = repr(self.op) if self.op is not None else 'None'
        return (f"<node.Node type={self.type}, value={self.value}, op={op_str}, "
                f"type_hint={self.type_hint}, children={self.children}, line={self.line}, col={self.col}>")