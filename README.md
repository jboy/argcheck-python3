argcheck-python3
================

Automated checking of Python3 function-call argument types &amp; values
using the `@validate_call` decorator.

Use of the `@validate_call` decorator enables you to remove verbose, repetitive
argument-checking boilerplate code from within the function.

The constraints upon argument types &amp; values are specified per-parameter
using [PEP-484 type hint annotations](https://peps.python.org/pep-0484/)
(`parameter_name: type_annotation`), extended using
the [PEP-593 `Annotated` type annotation](https://peps.python.org/pep-0593/)
(`Annotated[T, metadata]`) for value constraints as metadata.

If an argument check is violated when the decorated function is called,
an exception of type `argcheck.ArgCheckException` will be raised.

Example usage
-------------

```python
import argcheck as ac

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

Currently-implemented argument checks
-------------------------------------

- `isTypeEqualTo(specified_type)`: check the declared parameter type
- `isNotEmpty`: verify that a container of values is NOT empty
- `isMonotonicIncr`: verify that a sequence of values is monotonic increasing
- `isPositive`: verify that a numeric value is positive
- `eachAll(check)`: apply `check` to each value in a container; expect ALL true
