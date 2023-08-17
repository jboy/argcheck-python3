argcheck-python3
================

Automated checking of Python3 function-call argument types &amp; values
using the `@validate_call` decorator.

Use of `argcheck` enables you to remove verbose, repetitive argument-checking
boilerplate code from within the function, by instead annotating per-parameter
constraints.

Example usage
-------------

```python
import argcheck as ac
from typing import Sequence

@ac.validate_call
def construct_conv_net(
        in_channels: ac.Annotated[int, ac.isPositive] = 3,
        out_channels: ac.Annotated[int, ac.isPositive] = 1,
        num_features_per_scale: ac.Annotated[
                Sequence[int],
                [ac.isNotEmpty, ac.isMonotonicIncr, ac.eachAll(ac.isPositive)]
        ] = [64, 128, 256, 512],
    ):
    # Construct a Convolutional Neural Network...
```

Details
-------

The constraints upon argument types are specified per-parameter
using [PEP-484 type hint annotations](https://peps.python.org/pep-0484/)
(`parameter_name: type_annotation`), extended using
the [PEP-593 `Annotated` type annotation](https://peps.python.org/pep-0593/)
(`Annotated[T, metadata]`) for argument-value constraints as metadata.

Only annotated parameters are checked; you don't need to annotate
parameters if you don't care about checking their arguments.
Without the `@validate_call` decorator, `argcheck` annotations are
merely inert type hint annotations that conform to PEP-484 or PEP-593.

Arguments are only checked when the decorated function is called.
`argcheck` does not perform any static analysis of code.

`argcheck` is optimised for detailed error reporting rather than for speed
of checking.  `argcheck` is well-suited to large, infrequently-called
functions where it's important to validate arguments before expensive
mistakes occur.  `argcheck` might not be well-suited to frequently-called
functions if speed of execution is important.

If an argument check is violated when the decorated function is called,
an exception derived from `argcheck.ArgCheckException` will be raised.

A function decorated by `@validate_call` will present the same signature
as the original function, so other signature-introspection functionality
should also still work.

Currently-implemented argument checks
-------------------------------------

- `isTypeEqualTo(specified_type)`: check the declared parameter type
- `isNotEmpty`: verify that a container of values is NOT empty
- `isMonotonicIncr`: verify that a sequence of values is monotonic increasing
- `isPositive`: verify that a numeric value is positive
- `eachAll(check)`: apply `check` to each value in a container; expect ALL true
