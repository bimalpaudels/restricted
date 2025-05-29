### restricted: Enforcing Restrictions on Python Code Execution

## Overview

A lightweight Python package for analyzing and securely executing code blocks with AST-based restrictions. This package provides multiple execution methods, including direct execution, subprocesses, and `uv`, allowing for controlled execution with customizable allow/restrict lists.

## Demo

Live demo using the default settings.

[![Demo](https://github.com/user-attachments/assets/9f679859-5afa-49dd-b771-048452a2d7e9)](https://dotpy.bimals.net)

## Installation

### pip

```text
pip install restricted
```

### uv

```text
uv add restricted
```

## Usage

### With helper function

The helper function provides the easiest way to execute code with restrictions.

```python
from restricted.helpers import execute_restricted

# A block of code pretending to be malicious.
code = """
import os
print(os.getcwd())
"""

# Restrict specific modules
result = execute_restricted(code, method="direct", restrict=["os"])
print(result)

# Output: RestrictedImportError: 'os' is not allowed
```

#### Using allow lists

You can specify exactly what modules/functions are allowed instead of what's restricted.

```python
from restricted.helpers import execute_restricted

code = """
import math
print(math.sqrt(16))
"""

# Only allow specific modules
result = execute_restricted(code, method="direct", allow=["math", "print"])
print(result)

# Output: 4.0
```

#### Different execution methods

Choose from different execution methods based on your needs:

```python
from restricted.helpers import execute_restricted

code = """
print("Hello World")
"""

# Direct execution (fastest)
result = execute_restricted(code, method="direct", allow=["print"])

# Subprocess execution (more isolated)
result = execute_restricted(code, method="subprocess", allow=["print"])

# UV execution (using uv for isolation)
result = execute_restricted(code, method="uv", allow=["print"])
```

### Without helper function

For more advanced control over the execution process, you can use the Executor and Restrictor directly.

```python
from restricted.core import Executor, Restrictor

code = """
print("Hello World")
"""

# Create a restrictor with specific restrictions
restrictor = Restrictor(restrict=["os", "sys", "subprocess"])
executor = Executor(code, restrictor=restrictor)

# Execute with your preferred method
result = executor.execute(method="direct")
print(result)
```

### Using only the Restrictor

The `Restrictor` class can be used independently for validation without execution.

```python
from restricted.core import Restrictor

code = """
import os
print("Hello World")
"""

# Only validate, don't execute
restrictor = Restrictor(restrict=["os"])
try:
    validated_code = restrictor.restrict(code)
    print("Code is safe to execute")
except Exception as e:
    print(f"Code validation failed: {e}")
```

## API Reference

### Restrictor

- `allow`: Optional list of allowed modules/functions
- `restrict`: Optional list of restricted modules/functions
- Only one of `allow` or `restrict` can be provided

### Executor

- `method`: Execution method (`"direct"`, `"subprocess"`, or `"uv"`)
- Automatically applies restrictions before execution

### Exceptions

- `RestrictedImportError`: Raised when a restricted import is detected
- `RestrictedBuiltInsError`: Raised when a restricted built-in is used
- `ScriptExecutionError`: Raised when script execution fails

## Security Notice

**Caution**: Always ensure that the code you execute is thoroughly reviewed to avoid potential security risks. Malicious or unsafe code can harm the system or access sensitive resources. Consider running code in a controlled or isolated environment to minimize potential damage.

## Contribution

Any contributions to improve this project are welcome! If you have suggestions, bug fixes, or new features to propose,
feel free to submit a pull request on [GitHub](https://github.com/bimalpaudels/restricted).
