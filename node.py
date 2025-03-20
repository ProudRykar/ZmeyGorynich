# node.py
class Node:
    def __init__(self, type, value=None, children=None, op=None):
        self.type = type
        self.value = value
        self.children = children if children is not None else []
        self.op = op
        
    def __repr__(self):
        return f"<node.Node type={self.type}, value={self.value}, op={self.op}, children={self.children}>"