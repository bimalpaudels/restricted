import os, ast
import subprocess

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