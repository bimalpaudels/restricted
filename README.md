### Python Restrictor & Executor

## Overview
A sandboxed Python code execution environment with support for ast-based validation, restricted imports and builtins, and multiple execution methods including subprocesses and `uv`.

---
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

### Security Notice
This project is in early development and should not be considered production-ready for high-risk environments.

### Contribution
If you want to contribute to this small project, feel free to submit a
pull request [here](https://github.com/bimalpaudels/restricted).
