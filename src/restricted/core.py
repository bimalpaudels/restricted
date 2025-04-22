import os, ast
import subprocess

from src.restricted.exceptions import RestrictedBuiltInsError


class SyntaxParser:
    """
    Parses Python code using ast.parse() and raises exceptions for invalid syntax.
    """
    def __init__(self):
        self.code = None
        self.tree = None

    def _is_null_or_empty(self):
        if self.code is None or self.code == '':
            raise ValueError("Null or/and empty code")

    def parse_and_validate(self, code=None):
        """
        Parses the given Python code and returns the abstract syntax tree (AST).
        :param code: Python code as a string
        :return: AST tree
        """
        self.code = code
        self._is_null_or_empty()
        try:
            self.tree = ast.parse(self.code)
        except SyntaxError as e:
            raise SyntaxError(e.text)

        return self.tree


class Restrictor(ast.NodeVisitor):
    """
    """
    DEFAULT_RESTRICTED_MODULES = ["os", "sys", "requests"]
    DEFAULT_RESTRICTED_BUILTINS = ["open",]

    def __init__(self, restricted_modules=None, restricted_builtins=None, restrict_modules=True, restrict_builtins=True):
        self._restricted_modules = restricted_modules if restricted_modules is not None else self.DEFAULT_RESTRICTED_MODULES
        self._restricted_builtins = restricted_builtins if restricted_builtins is not None else self.DEFAULT_RESTRICTED_BUILTINS
        self._restrict_modules = restrict_modules
        self._restrict_builtins = restrict_builtins

    def visit_Import(self, node):
        """
        Checks for restricted modules in a node and raises an ImportError.
        :param node:
        """
        if self._restrict_modules:
            for alias in node.names:
                if alias.name in self._restricted_modules:
                    raise ImportError(f"'{alias.name}' is not allowed")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if self._restrict_modules:
            if node.module in self._restricted_builtins:
                raise ImportError(f"'{node.module}' is not allowed")
        self.generic_visit(node)

    def visit_Name(self, node):
        if self._restrict_builtins:
            if node.id in self._restricted_builtins:
                raise RestrictedBuiltInsError(f"'{node.id}' is not allowed")
        self.generic_visit(node)
