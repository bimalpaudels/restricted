from restricted.core import Restrictor, Executor
from typing import Optional, List


def execute_restricted(
    code: str,
    method: str,
    modules: Optional[List[str]] = None,
    builtins: Optional[List[str]] = None,
    action: Optional[str] = None,
):
    """
    Executes the given Python code in a restricted environment after applying restrictions.

    This helper function creates a `Restrictor` with the specified modules, builtins, and action,
    then uses an `Executor` to process and run the code using the given method.

    :param code: Python source code as a string.
    :param method: The execution method for the Executor ('direct', 'subprocess', or 'uv').
    :param modules: Optional list of module names to restrict or allow based on the action. Defaults to `Restrictor.DEFAULT_MODULES` if None.
    :param builtins: Optional list of built-in function names to restrict or allow based on the action. Defaults to `Restrictor.DEFAULT_BUILTINS` if None.
    :param action: The restriction action to apply ('restrict' or 'allow'). If None, the default Restrictor behavior will be used (action='restrict', default lists).
    :return: The result of executing the code.
    :raises ValueError: If the method is invalid or if no code is provided to the executor.
    :raises RestrictedImportError: If a restricted import is detected.
    :raises RestrictedBuiltInsError: If a restricted built-in is used.
    :raises ScriptExecutionError: If an error occurs during script execution.
    """

    restrictor = Restrictor(modules=modules, builtins=builtins, action=action)
    executor = Executor(code, restrictor=restrictor)
    return executor.execute(method=method)
