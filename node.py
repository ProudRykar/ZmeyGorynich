class Node:
    def __init__(self, type, value=None, children=None, op=None, type_hint=None, line=None, col=None):
        self.type = type
        self.value = value
        self.children = children if children is not None else []
        self.op = op
        self.type_hint = type_hint  # Для хранения аннотации типа (например, "строченька")
        self.line = line  # Номер строки
        self.col = col    # Номер столбца

    def __repr__(self):
        return (f"<node.Node type={self.type}, value={self.value}, op={self.op}, "
                f"type_hint={self.type_hint}, children={self.children}, line={self.line}, col={self.col}>")