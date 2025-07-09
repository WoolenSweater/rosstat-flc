from lark.tree import Tree
from lark.visitors import Transformer_InPlace


@staticmethod
def pop(children):
    return children.pop()


class Transformer(Transformer_InPlace):
    def __default__(self, data, children, meta):
        return children

    def _transform_tree(self, tree):
        tree.processing = True
        return self._call_userfunc(tree)


class MarkedTree(Tree):
    def __init__(self, data, children, meta=None):
        super().__init__(data, children, meta)
        self.processing = False
        self.contextual = True


class Context:
    def __init__(self):
        self.elems = []
        self.order = {}

    def __str__(self):
        return f"<Context elems={self.elems} order={self.order}"

    def add(self, elem):
        self.elems.append(elem)
        self.order.setdefault(elem.coords, len(self.elems) - 1)
        return elem

    def get(self, elem):
        try:
            return self.elems[self.order[elem.coords] + 1]
        except IndexError:
            return self.elems[self.order[elem.coords] - 1]
