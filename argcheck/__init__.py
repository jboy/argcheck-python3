"""Automated checking of Python3 function-call argument types & values
via the `@validate_call` decorator.

There are many like it; this one is mine.
"""

from .checks import *
from .exceptions import *
from .impl import Annotated, Sequence, validate_call
