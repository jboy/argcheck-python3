argcheck-python3
================

Automated checking of Python3 function-call argument types &amp; values
via the `@validate_call` decorator.

The constraints upon argument types &amp; values are specified per-parameter
using [PEP-484 type hint annotations](https://peps.python.org/pep-0484/)
(`parameter_name: type_annotation`), extended using
the [PEP-593 `Annotated` type annotation](https://peps.python.org/pep-0593/)
(`Annotated[T, metadata]`) for value constraints as metadata.

If an argument check is violated when the decorated function is called,
an exception of type `argcheck.ArgCheckException` will be raised.
