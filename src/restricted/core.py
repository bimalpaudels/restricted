import os
import ast
import subprocess
from typing import List, Optional

from restricted.exceptions import (
    RestrictedBuiltInsError,
    RestrictedImportError,
    ScriptExecutionError,
)
from restricted.utils import is_stdlib_module, is_builtin_function


class Restrictor(ast.NodeVisitor):
    """
    AST visitor that enforces restrictions on Python code by controlling access to modules and built-in functions.

    This class analyzes Python code's Abstract Syntax Tree (AST) and applies either allowlist or blocklist
    restrictions on imports and built-in function usage. It operates in two modes:
    - 'allow' mode: Only permits explicitly allowed modules/built-ins (allowlist approach)
    - 'restrict' mode: Blocks explicitly restricted modules/built-ins (blocklist approach)

    The restrictor validates import statements (both 'import' and 'from...import') and built-in function
    usage, raising appropriate exceptions when violations are detected.
    """

    def __init__(
        self,
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None,
    ):
        """
        Initialize the Restrictor with either an allowlist or blocklist of module/function names.

        Exactly one of 'whitelist' or 'blacklist' must be provided to define the restriction mode:
        - If 'whitelist' is provided: Only the specified modules/built-ins are permitted (allowlist mode)
        - If 'blacklist' is provided: The specified modules/built-ins are blocked (blocklist mode)

        Args:
            whitelist: List of module and built-in function names that are explicitly allowed.
                  When provided, all other standard library modules and built-ins are blocked.
            blacklist: List of module and built-in function names that are explicitly blocked.
                     When provided, all other modules and built-ins are allowed.

        Raises:
            ValueError: If neither 'whitelist' nor 'blacklist' is provided, or if both are provided.
        """
        self._whitelist = whitelist
        self._blacklist = blacklist
        self._verify_setup()

    def _verify_setup(self):
        """
        Validate the initialization parameters and configure the internal restriction mode.

        This method ensures that exactly one of 'whitelist' or 'blacklist' was provided during
        initialization, then sets up the internal '_action' and '_modules' attributes
        based on the provided configuration.

        Raises:
            ValueError: If neither 'whitelist' nor 'blacklist' is provided, or if both are provided.
        """
        if not self._whitelist and not self._blacklist:
            raise ValueError("Either whitelist or blacklist must be provided")

        if self._whitelist and self._blacklist:
            raise ValueError("Only one of whitelist or blacklist can be provided")

        if self._whitelist:
            self._action = "whitelist"
            self._modules = self._whitelist
        elif self._blacklist:
            self._action = "blacklist"
            self._modules = self._blacklist

    def check_syntax(self, code: Optional[str] = None, return_tree: bool = False):
        """
        Parse and validate the syntax of Python code, optionally returning the AST.

        This method parses the provided code string into an Abstract Syntax Tree (AST)
        and stores it as an instance attribute. It can either return the parsed AST
        or the unparsed code string representation.

        Args:
            code: Python source code string to parse and validate.
            return_tree: If True, returns the AST Module object; if False, returns
                        the unparsed string representation of the AST.

        Returns:
            ast.Module: The parsed AST if return_tree is True.
            str: The unparsed code string if return_tree is False.

        Raises:
            ValueError: If code is None or an empty string.
            SyntaxError: If the code contains invalid Python syntax.
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
        Apply the configured restrictions to Python code by analyzing its AST.

        This method parses the provided code, walks through its AST using the visitor pattern,
        and validates all import statements and built-in function usage against the configured
        restrictions. If any violations are found, appropriate exceptions are raised.

        Args:
            code: Python source code string to analyze and restrict.

        Returns:
            str: The unparsed code string representation after successful validation.

        Raises:
            ValueError: If code is None or empty (propagated from check_syntax).
            SyntaxError: If the code contains invalid Python syntax (propagated from check_syntax).
            RestrictedImportError: If an import statement violates the configured restrictions.
            RestrictedBuiltInsError: If a built-in function usage violates the configured restrictions.
        """
        tree = self.check_syntax(code, return_tree=True)
        if isinstance(tree, ast.Module):
            self.visit(tree)
            return ast.unparse(tree)

    def visit_Import(self, node):
        """
        Validate 'import' statements against the configured restrictions.

        This AST visitor method processes 'import module' statements and checks each
        imported module against the restriction configuration:
        - In 'blacklist' mode: Raises exception if any imported module is in the blacklist
        - In 'whitelist' mode: Raises exception if any standard library module is imported
          that is not in the whitelist

        Args:
            node: An ast.Import node representing an 'import ...' statement.

        Raises:
            RestrictedImportError: If any imported module violates the configured restrictions.
        """
        if self._action == "blacklist":
            for alias in node.names:
                if alias.name in self._modules:
                    raise RestrictedImportError(f"'{alias.name}' is not allowed")
        elif self._action == "whitelist":
            for alias in node.names:
                if is_stdlib_module(alias.name) and alias.name not in self._modules:
                    raise RestrictedImportError(f"'{alias.name}' is not allowed")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """
        Validate 'from...import' statements against the configured restrictions.

        This AST visitor method processes 'from module import name' statements and validates
        both the source module and imported names against the restriction configuration:
        - In 'blacklist' mode: Raises exception if the source module or any imported name
          is in the blacklist
        - In 'whitelist' mode: Raises exception if the source module or any imported standard
          library name is not in the whitelist

        Args:
            node: An ast.ImportFrom node representing a 'from ... import ...' statement.

        Raises:
            RestrictedImportError: If the source module or any imported name violates
                                 the configured restrictions.
        """
        if self._action == "blacklist":
            if node.module in self._modules:
                raise RestrictedImportError(f"'{node.module}' is not allowed")
            for alias in node.names:
                if alias.name in self._modules:
                    raise RestrictedImportError(f"'{alias.name}' is not allowed")

        elif self._action == "whitelist":
            if node.module:
                if is_stdlib_module(node.module) and node.module not in self._modules:
                    raise RestrictedImportError(f"'{node.module}' is not allowed")
                for alias in node.names:
                    if is_stdlib_module(alias.name) and alias.name not in self._modules:
                        raise RestrictedImportError(f"'{alias.name}' is not allowed")
        self.generic_visit(node)

    def visit_Name(self, node):
        """
        Validate name references (including built-in functions) against the configured restrictions.

        This AST visitor method processes name references in the code and validates
        built-in function usage against the restriction configuration:
        - In 'blacklist' mode: Raises exception if any name in the blacklist is referenced
        - In 'whitelist' mode: Raises exception if any built-in function is referenced
          that is not in the whitelist

        Args:
            node: An ast.Name node representing a name reference (variable, function, etc.).

        Raises:
            RestrictedBuiltInsError: If a built-in function reference violates the
                                   configured restrictions.
        """
        if self._action == "blacklist":
            if node.id in self._modules:
                raise RestrictedBuiltInsError(f"'{node.id}' is not allowed")
        elif self._action == "whitelist":
            if is_builtin_function(node.id) and node.id not in self._modules:
                raise RestrictedBuiltInsError(f"'{node.id}' is not allowed")
        self.generic_visit(node)


class Executor:
    """
    Execute Python code with applied restrictions in various execution environments.

    This class provides a convenient interface for executing Python code after applying
    restrictions using a Restrictor instance. It supports three execution methods:
    - Direct execution in the current process
    - Subprocess execution using the system Python interpreter
    - UV execution for isolated environments with dependency management

    The Executor automatically validates and restricts code before execution, ensuring
    that only permitted modules and built-in functions are used.
    """

    def __init__(
        self, code: Optional[str] = None, restrictor: Optional[Restrictor] = None
    ):
        """
        Initialize the Executor with optional code and restrictor configuration.

        If no restrictor is provided, a default Restrictor instance will be created,
        but this will raise a ValueError since the default Restrictor requires either
        'whitelist' or 'blacklist' parameters to be specified.

        Args:
            code: Python source code string to be processed and executed.
            restrictor: A configured Restrictor instance. If None, attempts to create
                       a default Restrictor (which will fail without whitelist/blacklist parameters).

        Raises:
            ValueError: If no restrictor is provided and the default Restrictor creation
                       fails due to missing whitelist/blacklist parameters, or if code validation
                       fails during the _validate() call.
        """
        self.code = code
        self.restrictor = restrictor if restrictor is not None else Restrictor()
        self._validate()

    def _validate(self):
        """
        Apply restrictions to the stored code using the configured restrictor.

        This method validates and restricts the code if it exists, updating the
        self.code attribute with the processed (but functionally equivalent) code.
        The restriction process analyzes the AST and raises exceptions if any
        violations are found, but does not modify the code structure.
        """
        if self.code is not None:
            self.code = self.restrictor.restrict(self.code)

    def _write_file_path(self):
        """
        Write the processed code to a temporary file in a sandbox directory.

        Creates a '.sandbox' directory in the current working directory (if it doesn't exist)
        and writes the current code to a file named 'script.py' within that directory.
        This temporary file is used for subprocess and UV execution methods.

        Returns:
            str: The absolute file path to the created script file.
        """
        sandbox_dir = os.path.join(os.getcwd(), ".sandbox")
        os.makedirs(sandbox_dir, exist_ok=True)

        script_file_path = os.path.join(sandbox_dir, "script.py")
        with open(script_file_path, "w") as f:
            f.write(self.code)  # type: ignore
        return script_file_path

    def execute(self, method: str, code: Optional[str] = None):
        """
        Execute the code using the specified execution method.

        This method supports three execution approaches:
        - 'direct': Execute code directly in the current Python process using exec()
        - 'subprocess': Execute code in a separate Python subprocess with timeout protection
        - 'uv': Execute code using UV for isolated environment with dependency management

        If new code is provided, it will be validated and restricted before execution,
        overriding any code provided during initialization.

        Args:
            method: Execution method - must be 'direct', 'subprocess', or 'uv'.
            code: Optional Python code to execute. If provided, overrides the
                 initialization code after applying restrictions.

        Returns:
            str: Standard output from subprocess/uv execution.
            None: For direct execution (output goes to current process stdout).

        Raises:
            ValueError: If no code is available (neither provided nor initialized),
                       or if the method is invalid.
            ScriptExecutionError: If subprocess or uv execution fails, times out,
                                 or encounters other execution errors.
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
        Execute code directly in the current Python process using exec().

        This method compiles the code and executes it directly within the current
        process context. It's the fastest execution method but provides no isolation
        from the host environment. Suitable for simple, trusted code without external
        dependencies or security concerns.

        Note: Output goes directly to the current process stdout/stderr.
        """
        compiled_code = compile(self.code, "<string>", "exec")  # type: ignore
        exec(compiled_code)

    def _subprocess_execution(self):
        """
        Execute code in a separate Python subprocess with timeout protection.

        This method writes the code to a temporary file and executes it using
        subprocess.run with the system Python interpreter. Provides process isolation
        and timeout protection (5 seconds). Recommended for code without external
        dependencies that needs isolation from the current process.

        Returns:
            str: The standard output from the executed script.

        Raises:
            ScriptExecutionError: If the subprocess returns a non-zero exit code,
                                 times out after 5 seconds, or encounters other
                                 execution errors. The error message includes the
                                 last line of stderr for debugging.
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
        Execute code using UV for isolated environment with dependency management.

        This method writes the code to a temporary file and executes it using 'uv run',
        which provides an isolated Python environment with automatic dependency management.
        UV can handle external dependencies and provides better isolation than subprocess
        execution. Includes timeout protection (5 seconds).

        Returns:
            str: The standard output from the executed script.

        Raises:
            ScriptExecutionError: If the UV subprocess returns a non-zero exit code,
                                 times out after 5 seconds, or encounters other
                                 execution errors. The error message includes the
                                 last line of stderr for debugging.
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
