from lark.tree import Tree as BaseTree
from lark.visitors import Transformer_InPlace as BaseTransformer


def lazy(tree):
    return not any(tree.scan_values(lambda token: token == "or"))


class Transformer(BaseTransformer):
    def _transform_tree(self, tree):
        tree.processing = True
        return self._call_userfunc(tree)


class Tree(BaseTree):
    _meta = None

    def __init__(self, data, children, meta=None):
        self.data = data
        self.children = children
        self.processing = False
