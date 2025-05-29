from restricted.core import Restrictor, Executor
from typing import Optional, List


def execute_restricted(
    code: str,
    method: str,
    allow: Optional[List[str]] = None,
    restrict: Optional[List[str]] = None,
):
    """
    Executes the given Python code in a restricted environment after applying restrictions using either an allow list or a restrict list.

    This helper function creates a `Restrictor` with the specified allow or restrict list,
    then uses an `Executor` to process and run the code using the given method.

    :param code: Python source code as a string.
    :param method: The execution method for the Executor ('direct', 'subprocess', or 'uv').
    :param allow: Optional list of names that are allowed. If provided, the action is 'allow'. Defaults to None.
    :param restrict: Optional list of names that are restricted. If provided, the action is 'restrict'. Defaults to None.
    :return: The result of executing the code.
    :raises ValueError: If the method is invalid, if no code is provided to the executor, or if neither `allow` nor `restrict` are provided, or if both are provided during Restrictor initialization.
    :raises RestrictedImportError: If a restricted import is detected.
    :raises RestrictedBuiltInsError: If a restricted built-in is used.
    :raises ScriptExecutionError: If an error occurs during script execution.
    """

    restrictor = Restrictor(allow=allow, restrict=restrict)
    executor = Executor(code, restrictor=restrictor)
    return executor.execute(method=method)
