"""Automated checking of Python3 function-call argument types & values
via the `@validate_call` decorator.

There are many like it; this one is mine.

Project repo with LICENSE and tests: https://github.com/jboy/argcheck-python3
"""

from .checks import *
from .exceptions import *
from .impl import Annotated, Sequence, validate_call
