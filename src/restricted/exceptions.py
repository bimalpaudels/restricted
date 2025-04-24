class RestrictedBuiltInsError(Exception):
    """
    Raised when a restricted builtin is used.
    """
    pass

class RestrictedImportError(Exception):
    """
    Raised when a restricted import is used.
    """