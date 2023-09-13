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

Currently-implemented argument checks
-------------------------------------

- `isTypeEqualTo(specified_type)`: check for equality to declared parameter type
- `isTypeOfSequence(specified_type)`: check for a sequence type
- `isNotEmpty`: verify that a container of values is NOT empty
- `isMonotonicIncr`: verify that a sequence of values is monotonic increasing
- `isPositive`: verify that a numeric value is positive
- `eachAll(check)`: apply `check` to each value in a container; expect ALL true

Syntax
------

(The syntax is demonstrated in the "Example usage" above.)

The constraints upon argument types are specified per-parameter
using [PEP-484 type hint annotations](https://peps.python.org/pep-0484/)
(`parameter_name: type_annotation`), extended using
the [PEP-593 `Annotated` type annotation](https://peps.python.org/pep-0593/)
(`Annotated[T, metadata]`) for argument-value constraints as metadata.

Only annotated parameters are checked; you don't need to annotate
parameters if you don't care about checking their arguments.
Without the `@validate_call` decorator, `argcheck` annotations are
merely inert type hint annotations that conform to PEP-484 or PEP-593.

What `argcheck` does / does not
-------------------------------

Arguments are only checked when the decorated function is called.
`argcheck` does not perform any static analysis of code.

If an argument check is violated when the decorated function is called,
an exception derived from `argcheck.ArgCheckException` will be raised.

`argcheck` is optimised for detailed error reporting rather than for speed
of checking.  `argcheck` is well-suited to large, infrequently-called
functions where it's important to validate arguments before expensive
mistakes occur.  `argcheck` might not be well-suited to frequently-called
functions if speed of execution is important.

A function decorated by `@validate_call` will present the same signature
as the original function, so other signature-introspection functionality
should also still work.

Use of generic Sequence type `typing.Sequence[T]`
-------------------------------------------------

This code was originally written on Python 3.5, so it uses
[`typing.Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)
rather than
[`collections.abc.Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)
as its "generic Sequence" type:

- [https://docs.python.org/3/library/typing.html#typing.Sequence](https://docs.python.org/3/library/typing.html#typing.Sequence)
- [https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence)

Why?

Gather round, kids, while grampa tells you a story about the Before Time...

Before Python3.9,
`typing.Sequence` was a distinct type from `collections.abc.Sequence`:

```python
# in file `/usr/lib/python3.5/typing.py`:

if hasattr(collections_abc, 'Reversible'):
    class Sequence(Sized, Reversible[T_co], Container[T_co],
               extra=collections_abc.Sequence):
        pass
else:
    class Sequence(Sized, Iterable[T_co], Container[T_co],
                   extra=collections_abc.Sequence):
        pass
```

But from Python3.9 onwards:
`typing.Sequence` is now merely an alias for `collections.abc.Sequence`:

```python
# in file `/usr/lib/python3.10/typing.py`:

Sequence = _alias(collections.abc.Sequence, 1)
```

Also, before Python3.9,
`collections.abc.Sequence` didn't support subscripting (`[]`),
which is needed to enable a generic alias type in annotations.
Only `typing.Sequence` supported subscripting:

```python
>>> import sys; sys.version
'3.5.2 (default, Jan 26 2021, 13:30:48) \n[GCC 5.4.0 20160609]'
>>> from typing import Sequence as typ_Seq
>>> from collections.abc import Sequence as abc_Seq
>>> typ_Seq[int]
typing.Sequence<+T_co>[int]
>>> abc_Seq[int]
Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    TypeError: 'ABCMeta' object is not subscriptable
>>>
```

But from Python3.9 onwards:

```python
>>> import sys; sys.version
'3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0]'
>>> from typing import Sequence as typ_Seq
>>> from collections.abc import Sequence as abc_Seq
>>> typ_Seq[int]
typing.Sequence[int]
>>> abc_Seq[int]
collections.abc.Sequence[int]
>>>
```

Also, before Python 3.7,
you could use `isinstance(value, type)` to check generic types:

```python
>>> some_list = [1, 2, 3]
>>> isinstance(some_list, typ_Seq[int])
True
```

But from Python3.7 onwards:

```python
>>> some_list = [1, 2, 3]
>>> isinstance(some_list, typ_Seq[int])
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib/python3.10/typing.py", line 994, in __instancecheck__
    return self.__subclasscheck__(type(obj))
  File "/usr/lib/python3.10/typing.py", line 997, in __subclasscheck__
    raise TypeError("Subscripted generics cannot be used with"
TypeError: Subscripted generics cannot be used with class and instance checks
>>> isinstance(some_list, abc_Seq[int])
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: isinstance() argument 2 cannot be a parameterized generic
```

Here is a Stack Overflow question about this,
from someone with the same problem:
[https://stackoverflow.com/questions/53854463/python-3-7-check-if-type-annotation-is-subclass-of-generic](https://stackoverflow.com/questions/53854463/python-3-7-check-if-type-annotation-is-subclass-of-generic)

So this caused the hasty definition of a new class `checks.isTypeOfSequence`
when I encountered this problem on a deployment to a Python3.10 system!
