import builtins
import sys


def is_stdlib_module(name: str) -> bool:
    """
    Check if a module is a built-in module.
    """
    return name in sys.stdlib_module_names


def is_builtin_function(name: str) -> bool:
    """
    Check if a function is a built-in function.
    """
    return hasattr(builtins, name) and callable(getattr(builtins, name))
