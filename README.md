### restricted: Enforcing Restrictions on Python Code Execution

## Overview
A Python code execution environment with support for restricting imports, built-ins with AST-based validation. This package provides multiple execution methods, including subprocesses and `uv`, allowing for controlled execution with customizable restrictions on potentially unsafe code.

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
The helper function could be used to execute code block the easiest with uv. 
```python
from restricted.helpers import execute_restricted

# A block of code pretending to be malicious.
code="""
import os
print(os.getcwd())
"""

print(execute_restricted(code))

# Shell Output
ImportError: 'os' is not allowed
```

#### Custom restrictions
You can provide your own restricting modules and built-in functions to restrict.
```python
from restricted.helpers import execute_restricted
...
custom_restricted_modules = ["os", "sys", "asyncio", 'builtins'] 
custom_restricted_builtins = ["print", "open", "min", "max"]

result = execute_restricted(code, restricted_modules=custom_restricted_modules, restricted_builtins=custom_restricted_builtins)
```

#### Execute without restriction
During development, code could be tested without restrictions by passing the `restrict=False` flag to the helper function.
```python
from restricted.helpers import execute_restricted

# A block of code pretending to be malicious.
code="""
import os
print(os.getcwd())
"""

print(execute_restricted(code, restrict=False))

# Shell Output
home/foo/projects/somefolder
```
### Without helper function
For more advanced control over the execution process, you can use the Executor directly. This approach allows you to manage both the restriction and the execution method.
```python
from restricted.core import Executor, Restrictor
code="""
print("Hello World")
"""
custom_restricted_modules = ["os", "sys", "asyncio", 'builtins'] 

custom_restrictor = Restrictor(restricted_modules=custom_restricted_modules)
executor = Executor(code, restrictor=custom_restrictor)

# Different execution methods
executor.direct_execution() or executor.subprocess_execution()
...
```
### Using only the Restrictor
It's not necessary to always use the Executor. Many use cases could need just the validation and not the execution. 
The `Restrictor` class can be used on it's own for finer control with execution behavior.
```python
from restricted.core import Restrictor, SyntaxParser
code="""
print("Hello World")
"""
tree = SyntaxParser().parse_and_validate(code=code)

# Only restrict certain modules
custom_restricted_modules = ["os", "sys", "asyncio", 'builtins'] 
restrictor = Restrictor(restrict_modules=True, restrict_builtins=False, restricted_modules=custom_restricted_modules)

# Only restrict certain built-ins
custom_restricted_builtins = ["print", "open", "min", "max"]
restrictor = Restrictor(restrict_modules=False, restrict_builtins=True, restricted_builtins=custom_restricted_builtins)

# Visit the nodes
restrictor.visit(tree)
```

## Security Notice
**Caution**: Always ensure that the code you execute is thoroughly reviewed to avoid potential security risks. Malicious or unsafe code can harm the system or access sensitive resources. Consider running code in a controlled or isolated environment to minimize potential damage.

## Contribution
Any contributions to improve this project are welcome! If you have suggestions, bug fixes, or new features to propose, 
feel free to submit a pull request on [GitHub](https://github.com/bimalpaudels/restricted). 

