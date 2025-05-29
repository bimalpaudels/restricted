import builtins
import sys


def is_stdlib_module(name: str) -> bool:
    """
    Check if a module name corresponds to a Python standard library module.

    This function determines whether the given module name is part of Python's
    standard library by checking against sys.stdlib_module_names, which contains
    the names of all modules that are part of the standard library for the
    current Python installation.

    Args:
        name: The module name to check (e.g., 'os', 'sys', 'json').

    Returns:
        bool: True if the module is part of the standard library, False otherwise.
    """
    return name in sys.stdlib_module_names


def is_builtin_function(name: str) -> bool:
    """
    Check if a name corresponds to a Python built-in function.

    This function determines whether the given name is a built-in function by
    checking if it exists as an attribute in the builtins module and is callable.
    Built-in functions are those available in the global namespace without any
    imports (e.g., print, len, str, int).

    Args:
        name: The function name to check (e.g., 'print', 'len', 'open').

    Returns:
        bool: True if the name is a built-in function, False otherwise.
    """
    return hasattr(builtins, name) and callable(getattr(builtins, name))
