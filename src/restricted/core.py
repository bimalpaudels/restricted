import os, ast
import subprocess

from restricted.exceptions import RestrictedBuiltInsError


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


class Executor:
    def __init__(self, code, restrict=True, restrictor:Restrictor=None):
        self.code = code
        self.parser = SyntaxParser()
        self.unparsed = None
        self.restrict = restrict
        self.restrictor = restrictor if restrictor is not None else Restrictor()
        self._validate()

    def _validate(self):
        """Validates the code block by first parsing into ast node and then visiting with restrictor.
        If self.restrict=False(Default=True), the entire code block can be executed right after parsing."""
        tree = self.parser.parse_and_validate(self.code)
        if self.restrict:
            self.restrictor.visit(tree)
        self.unparsed = ast.unparse(tree)

    def _write_file_path(self):
        sandbox_dir = os.path.join(os.getcwd(), ".sandbox")
        os.makedirs(sandbox_dir, exist_ok=True)

        script_file_path = os.path.join(sandbox_dir, "script.py")
        with open(script_file_path, "w") as f:
            f.write(self.unparsed)
        return script_file_path

    def direct_execution(self):
        """
        Executes the code directly on the system using exec. Useful to test with codes
        that have no dependencies and are not potentially harmful on execution.
        :return:
        """
        compiled_code = compile(self.code, '<string>', 'exec')
        exec(compiled_code)

    def subprocess_execution(self):
        """
        Writes the code into a file and uses subprocess and uses 'python' command to execute it. Recommended
        for code without any dependencies and installations. If dependencies have to be installed, use execute_with_uv().
        :return:
        """
        script_file_path = self._write_file_path()
        try:
            result = subprocess.run(
                ["python", script_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if result.stderr != "":
                return result.stderr
            else:
                return result.stdout
        except subprocess.TimeoutExpired:
            return subprocess.TimeoutExpired
        except Exception as e:
            raise e

    def execute_with_uv(self):
        """
        Writes the code into a file and uses subprocess and 'uv' to execute it. Recommended
        for code with dependencies and installations because uv creates an isolated environment
        to execute the file.

        :return: stdout or stderr
        """
        script_file_path = self._write_file_path()
        try:
            result = subprocess.run(
                ['uv', 'run', script_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if result.stderr != "":
                return result.stderr
            else:
                return result.stdout
        except subprocess.TimeoutExpired:
            return subprocess.TimeoutExpired
        except Exception as e:
            raise e