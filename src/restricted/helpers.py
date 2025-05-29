from restricted.core import Restrictor, Executor
from typing import Optional, List


def execute_restricted(
    code: str,
    method: str,
    whitelist: Optional[List[str]] = None,
    blacklist: Optional[List[str]] = None,
):
    """
    Executes the given Python code in a restricted environment after applying restrictions using either an whitelist or a blacklist.

    This helper function creates a `Restrictor` with the specified whitelist or blacklist,
    then uses an `Executor` to process and run the code using the given method.

    :param code: Python source code as a string.
    :param method: The execution method for the Executor ('direct', 'subprocess', or 'uv').
    :param whitelist: Optional list of names that are allowed. If provided, the action is 'whitelist'. Defaults to None.
    :param blacklist: Optional list of names that are restricted. If provided, the action is 'blacklist'. Defaults to None.
    :return: The result of executing the code.
    :raises ValueError: If the method is invalid, if no code is provided to the executor, or if neither `whitelist` nor `blacklist` are provided, or if both are provided during Restrictor initialization.
    :raises RestrictedImportError: If a restricted import is detected.
    :raises RestrictedBuiltInsError: If a restricted built-in is used.
    :raises ScriptExecutionError: If an error occurs during script execution.
    """

    restrictor = Restrictor(whitelist=whitelist, blacklist=blacklist)
    executor = Executor(code, restrictor=restrictor)
    return executor.execute(method=method)
