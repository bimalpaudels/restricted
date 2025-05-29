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

        :raises ValueError: If the code is None or empty.
        """
        if self.code is None or self.code == "":
            raise ValueError("Null or/and empty code")

    def parse_and_validate(self, code=None):
        """
        Parses the given Python code and returns the abstract syntax tree (AST) after validation.

        :param code: A string containing valid Python code to parse. Defaults to None.
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
    exceptions when restricted modules are imported or when forbidden built-in functions are used, based on the configured action ('restrict' or 'allow').
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
        Initializes the Restrictor with optional custom restrictions on modules and built-in functions and the action to perform.

        :param modules: Optional list of module names. Used with 'restrict' or 'allow' action. Defaults to `DEFAULT_MODULES` if not provided.
        :param builtins: Optional list of built-in function names. Used with 'restrict' or 'allow' action. Defaults to `DEFAULT_BUILTINS` if not provided.
        :param action: The action to perform ('restrict' or 'allow'). Must be provided.
        :raises ValueError: If the action is not set or is invalid.
        """
        self._modules = modules if modules is not None else self.DEFAULT_MODULES
        self._builtins = builtins if builtins is not None else self.DEFAULT_BUILTINS
        self._action = action
        self._verify_setup()

    def _verify_setup(self):
        """
        Verifies that the setup is correct, specifically that the action is set and is valid.

        :raises ValueError: If the action is not set or is invalid.
        """
        if not self._action:
            raise ValueError("Action is not set. Must be 'restrict' or 'allow'.")

        if self._action not in ["restrict", "allow"]:
            raise ValueError("Invalid action. Must be 'restrict' or 'allow'.")

    def check_syntax(self, code: Optional[str] = None, return_tree: bool = False):
        """
        Checks the syntax of the code and optionally returns the AST.

        :param code: The Python code string to check.
        :param return_tree: If True, returns the AST; otherwise, returns the unparsed code. Defaults to False.
        :return: The AST or the unparsed code string.
        :raises ValueError: If the code is None or empty.
        :raises SyntaxError: If the code contains invalid Python syntax.
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
        Applies the configured restrictions to the provided code.

        :param code: The Python code string to restrict.
        :return: The unparsed, restricted code string.
        :raises ValueError: If the code is None or empty (from check_syntax).
        :raises SyntaxError: If the code contains invalid Python syntax (from check_syntax).
        :raises RestrictedImportError: If a restricted module is imported and action is 'restrict', or an unallowed module is imported and action is 'allow'.
        :raises RestrictedBuiltInsError: If a restricted builtin is used and action is 'restrict', or an unallowed builtin is used and action is 'allow'.
        """
        tree = self.check_syntax(code, return_tree=True)
        if isinstance(tree, ast.Module):
            self.visit(tree)
            return ast.unparse(tree)

    def visit_Import(self, node):
        """
        Visits an 'Import' AST node and checks against the configured module list based on the action.
        Raises RestrictedImportError if a violation is detected.

        :param node: An `ast.Import` node representing an 'import ...' statement.
        :raises RestrictedImportError: If the module is not allowed based on the action.
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
        Visits an 'ImportFrom' AST node and checks against the configured module list based on the action.
        Raises RestrictedImportError if a violation is detected.

        :param node: An `ast.ImportFrom` node representing a 'from ... import ...' statement.
        :raises RestrictedImportError: If the source module or any imported member is not allowed based on the action.
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
        Visits a 'Name' AST node and checks against the configured builtin list based on the action.
        Raises RestrictedBuiltInsError if a violation is detected.

        :param node: An `ast.Name` node representing a name, potentially a built-in function call.
        :raises RestrictedBuiltInsError: If the name is not allowed based on the action.
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
    This class provides a convenient way to execute restricted code after applying restrictions using the `Restrictor`.
    Users can also use the `Restrictor` independently and implement their own execution logic.
    """

    def __init__(
        self, code: Optional[str] = None, restrictor: Optional[Restrictor] = None
    ):
        """
        Initializes the Executor with the provided source code and an optional Restrictor instance.

        :param code: A string of Python source code to be processed and executed. Defaults to None.
        :param restrictor: An optional Restrictor instance. If not provided, a default Restrictor with 'restrict' action and default lists is created.
        """
        self.code = code
        self.restrictor = restrictor if restrictor is not None else Restrictor()
        self._validate()

    def _validate(self):
        """Validates the code block by first parsing into ast node and then visiting with the configured restrictor.
        Restrictions are applied here if a restrictor is configured.
        """
        if self.code is not None:
            self.code = self.restrictor.restrict(self.code)

    def _write_file_path(self):
        """
        Writes the current processed code to a file named 'script.py' inside a '.sandbox' directory
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

    def execute(self, method: str, code: Optional[str] = None):
        """
        Executes the stored or provided code using the specified method.

        :param method: The execution method. Must be 'direct', 'subprocess', or 'uv'.
        :param code: Optional Python code string to execute. If provided, it overrides the code provided during initialization.
        :return: The stdout from subprocess or uv execution, or None for direct execution.
        :raises ValueError: If no code is provided and no code was initialized, or if the method is invalid.
        :raises ScriptExecutionError: If an error occurs during subprocess or uv execution.
        """
        if code is None and self.code is None:
            raise ValueError(
                "Code needs to be provided, either during initialization or when executing."
            )

        if code is not None:  # If code is provided, override the code from init
            self.code = self.restrictor.restrict(code)

        if method is None or method not in ["direct", "subprocess", "uv"]:
            raise ValueError("Invalid method. Must be 'direct', 'subprocess', or 'uv'.")

        if method == "direct":
            self._direct_execution()
        elif method == "subprocess":
            return self._subprocess_execution()
        elif method == "uv":
            return self._execute_with_uv()

    def _direct_execution(self):
        """
        Executes the code directly in the current process using `exec`.
        Suitable for simple codes with no dependencies and low risk.
        """
        compiled_code = compile(self.code, "<string>", "exec")  # type: ignore
        exec(compiled_code)

    def _subprocess_execution(self):
        """
        Writes the code to a temporary file and executes it using `subprocess.run` with the 'python' command.
        Recommended for code without external dependencies.

        :return: The standard output of the executed script.
        :raises ScriptExecutionError: If the subprocess fails or times out.
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
        Writes the code to a temporary file and executes it using `uv run`.
        Recommended for code with external dependencies as `uv` manages an isolated environment.

        :return: The standard output of the executed script.
        :raises ScriptExecutionError: If the uv subprocess fails or times out.
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
