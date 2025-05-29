import os
import ast
import subprocess
from typing import Optional

from restricted.exceptions import (
    RestrictedBuiltInsError,
    RestrictedImportError,
    ScriptExecutionError,
)


class SyntaxParser:
    """
    A utility class for parsing Python source code into an abstract syntax tree (AST)
    using Python's built-in `ast` module. Validates the input and raises exceptions for empty input or syntax errors.
    """

    def __init__(self):
        """
        Initializes the parser with empty code and AST tree placeholders.
        """
        self.code = None
        self.tree = None

    def _is_null_or_empty(self):
        """
        Checks whether the provided code is None or an empty string.

        :raises: ValueError: If the code is None or empty.
        """
        if self.code is None or self.code == "":
            raise ValueError("Null or/and empty code")

    def parse_and_validate(self, code=None):
        """
        Parses the given Python code and returns the abstract syntax tree (AST) after validation.

        :param code: A string containing valid Python code to parse.
        :return: The parsed AST (abstract syntax tree) object.

        :raises ValueError: If the provided code is None or empty.
        :raises SyntaxError: If the code contains invalid Python syntax.
        """
        self.code = code
        self._is_null_or_empty()
        try:
            self.tree = ast.parse(self.code)  # type: ignore
        except SyntaxError as e:
            raise SyntaxError(e.text)

        return self.tree


class Restrictor(ast.NodeVisitor):
    """
    AST visitor that enforces restrictions on the use of specific modules and built-in functions
    in a given Python code snippet. This is designed to walk through the abstract syntax tree (AST) of Python code and raise
    exceptions when restricted modules are imported or when forbidden built-in functions are used.
    """

    DEFAULT_MODULES = ["os", "sys", "requests"]
    DEFAULT_BUILTINS = [
        "open",
    ]

    def __init__(
        self,
        modules=None,
        builtins=None,
        action=None,
    ):
        """
        Initializes the Restrictor with optional custom restrictions on modules and built-in functions.

        :param restricted_modules: Optional list of module names to restrict. Defaults to
                                   `DEFAULT_RESTRICTED_MODULES` if not provided.
        :param restricted_builtins: Optional list of built-in function names to restrict. Defaults to
                                    `DEFAULT_RESTRICTED_BUILTINS` if not provided.
        :param restrict_modules: Flag indicating whether to enforce restrictions on module imports.
        :param restrict_builtins: Flag indicating whether to enforce restrictions on built-ins.
        """
        self._modules = modules if modules is not None else self.DEFAULT_MODULES
        self._builtins = builtins if builtins is not None else self.DEFAULT_BUILTINS
        self._action = action
        self._verify_setup()

    def _verify_setup(self):
        """
        Verifies that the setup is correct.
        """
        if not self._action:
            raise ValueError("Action is not set. Must be 'restrict' or 'whitelist'.")

        if self._action not in ["restrict", "allow"]:
            raise ValueError("Invalid action. Must be 'restrict' or 'allow'.")

    def check_syntax(self, code: Optional[str] = None, return_tree: bool = False):
        """
        Checks the syntax of the code.
        """
        if code is None or code == "":
            raise ValueError("Null and/or empty code")
        try:
            self.tree = ast.parse(code)
        except SyntaxError as e:
            raise SyntaxError(e.text)
        if return_tree:
            return self.tree
        return ast.unparse(self.tree)

    def restrict(self, code: Optional[str] = None):
        """
        Restricts the code.
        """
        tree = self.check_syntax(code, return_tree=True)
        if isinstance(tree, ast.Module):
            self.visit(tree)
            return ast.unparse(tree)

    def visit_Import(self, node):
        """
        Visits an 'Import' AST node and checks whether the module is in the list of restricted modules.
        Raises an ImportError if a restricted module is detected.

        :param node: An `ast.Import` node representing an 'import ...' statement.
        :raises: ImportError: If the module is in the restricted list.
        """
        if self._action == "restrict":
            for alias in node.names:
                if alias.name in self._modules:
                    raise RestrictedImportError(f"'{alias.name}' is not allowed")
        elif self._action == "allow":
            for alias in node.names:
                if alias.name not in self._modules:
                    raise RestrictedImportError(f"'{alias.name}' is not allowed")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """
        Visits an 'ImportFrom' AST node and checks whether the module or any of its imported members
        are in the list of restricted modules. Raises an ImportError if a restricted module or member
        is detected.
        This method provides additional enforcement beyond `visit_Import()` by inspecting both the
        source module (`from module import ...`) and each imported name individually.

        :param node: An `ast.ImportFrom` node representing a 'from ... import ...' statement.
        :raises ImportError: If the source module or any imported member is in the restricted list.
        """
        if self._action == "restrict":
            if node.module in self._modules:
                raise RestrictedImportError(f"'{node.module}' is not allowed")
            for alias in node.names:
                if alias.name in self._modules:
                    raise RestrictedImportError(f"'{alias.name}' is not allowed")
        elif self._action == "allow":
            if node.module not in self._modules:
                raise RestrictedImportError(f"'{node.module}' is not allowed")
            for alias in node.names:
                if alias.name not in self._modules:
                    raise RestrictedImportError(f"'{alias.name}' is not allowed")
        self.generic_visit(node)

    def visit_Name(self, node):
        """
        Visits a 'Name' AST node and checks whether the node id is in the list of restricted builtin methods.
        Raises an ImportError if a method is detected.

        :param node: An `ast.Name` node representing a '...()' expression. For e.g. with open()...
        :raises: ImportError: If the function is in the restricted list.
        """
        if self._action == "restrict":
            if node.id in self._builtins:
                raise RestrictedBuiltInsError(f"'{node.id}' is not allowed")
        elif self._action == "allow":
            if node.id not in self._builtins:
                raise RestrictedBuiltInsError(f"'{node.id}' is not allowed")
        self.generic_visit(node)


class Executor:
    """
    This class provides a convenient way execute the restricted code using the `Restrictor`,
    but using the `Restrictor` independently is also supported. After validation, users can
    implement their own execution logic if desired.
    """

    def __init__(
        self, code: Optional[str] = None, restrictor: Optional[Restrictor] = None
    ):
        """
        Initializes the Executor with the provided source code and optional restriction settings.

        :param code: A string of Python source code to be parsed and optionally validated.
        :param restrict: Boolean flag to enable or disable code restriction checks. Defaults to True.
        :param restrictor: An optional Restrictor instance. If not provided, a default Restrictor is created.
        """
        self.code = code
        self.restrictor = restrictor if restrictor is not None else Restrictor()
        self._validate()

    def _validate(self):
        """Validates the code block by first parsing into ast node and then visiting with restrictor.
        If self.restrict=False(Default=True), the entire restriction can be skipped after parsing."""
        if self.code is not None:
            self.code = self.restrictor.restrict(self.code)

    def _write_file_path(self):
        """
        Writes the current unparsed code to a file named 'script.py' inside a '.sandbox' directory
        in the current working directory.

        This method ensures the sandbox directory exists, writes the code to a file, and returns
        the full path to the written script.

        :return: Full file path to the saved script.
        """
        sandbox_dir = os.path.join(os.getcwd(), ".sandbox")
        os.makedirs(sandbox_dir, exist_ok=True)

        script_file_path = os.path.join(sandbox_dir, "script.py")
        with open(script_file_path, "w") as f:
            f.write(self.code)  # type: ignore
        return script_file_path

    def execute(self, code: Optional[str] = None, method: str = "direct"):
        if code is None and self.code is None:
            raise ValueError(
                "Code needs to be provided, either during initialization or when executing."
            )

        if code is not None:  # If code is provided, override the code from init
            self.code = self.restrictor.restrict(code)

        if method not in ["direct", "subprocess", "uv"]:
            raise ValueError("Invalid method. Must be 'direct', 'subprocess', or 'uv'.")

        if method == "direct":
            self._direct_execution()
        elif method == "subprocess":
            return self._subprocess_execution()
        elif method == "uv":
            return self._execute_with_uv()

    def _direct_execution(self):
        """
        Executes the code directly on the system using exec. Useful to test with codes
        that have no dependencies and are not potentially harmful on execution.
        :return:
        """
        compiled_code = compile(self.code, "<string>", "exec")  # type: ignore
        exec(compiled_code)

    def _subprocess_execution(self):
        """
        Writes the code into a file and uses subprocess and uses 'python' command to execute it. Recommended
        for code without any dependencies and installations. If dependencies have to be installed, use execute_with_uv().
        :return: stdout or stderr
        """
        script_file_path = self._write_file_path()
        try:
            result = subprocess.run(
                ["python", script_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            err = e.stderr.splitlines()
            raise ScriptExecutionError(err[-1])

        except subprocess.TimeoutExpired as e:
            raise ScriptExecutionError(
                f"TimeoutExpired: Script took longer than {e.timeout} seconds."
            )

        except Exception as e:
            raise ScriptExecutionError(f"Unhandled exception: {e}")

    def _execute_with_uv(self):
        """
        Writes the code into a file and uses subprocess and 'uv' to execute it. Recommended
        for code with dependencies and installations because uv creates an isolated environment
        to execute the file.

        :return: stdout or stderr
        """
        script_file_path = self._write_file_path()
        try:
            result = subprocess.run(
                ["uv", "run", script_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            err = e.stderr.splitlines()
            raise ScriptExecutionError(err[-1])

        except subprocess.TimeoutExpired as e:
            raise ScriptExecutionError(
                f"TimeoutExpired: Script took longer than {e.timeout} seconds."
            )

        except Exception as e:
            raise ScriptExecutionError(f"Unhandled exception: {e}")
