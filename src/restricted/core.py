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