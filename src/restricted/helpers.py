from restricted.core import Restrictor, Executor
from typing import Optional, List


def execute_restricted(
        code:str,
        restricted_modules: Optional[List[str]] = None,
        restricted_builtins: Optional[List[str]] = None,
):
    """
    :param code: Python code to execute
    :param restricted_modules: Modules to block (None for defaults)
    :param restricted_builtins: Builtin modules to block (None for defaults)
    :return: Result of code execution
    """

    restrictor = Restrictor(restricted_modules=restricted_modules, restricted_builtins=restricted_builtins)
    executor = Executor(code, restrictor=restrictor)
    return executor.execute_with_uv()
