"""Return a `repr` string that can be used to re-create its argument.

Specifically, if the argument to parameter `x` is a value of type `type`,
this function will return a useful string representation of the value,
rather than the unhelpful representation returned by Python by default
if you call `repr(x)` on a type.

That's quite an abstract explanation.  An example will help to clarify:

Let's say that `x` has the value `int` (the type of integers in Python):

    >>> x = int

Now `x` has type `type`:

    >>> type(x)
    <class 'type'>

If you call `repr(x)`, the string representation will be `"<class 'int'>"`:

    >>> repr(x)
    "<class 'int'>"

Observe that the string `"<class 'int'>"` is not valid Python code;
rather, it looks like some sort of pseudo-XML.  But the Python docs say
the following about the string returned by `repr`:

    If at all possible, this should look like a valid Python expression
    that could be used to recreate an object with the same value (given
    an appropriate environment). If this is not possible, a string of
    the form `<...some useful description...>` should be returned.
    -- https://docs.python.org/3/reference/datamodel.html#object.__repr__

An expression that could be used to recreate the value of our variable `x`
is simply `int`:

    >>> x
    <class 'int'>
    >>> int
    <class 'int'>

There are hand-wavey excuses about module imports for the behaviour of the
default Python `repr`:

    And, despite the words on the subject found in typical docs,
    hardly anybody bothers making the `__repr__` of objects be a string
    that `eval` may use to build an equal object (it's just too hard,
    AND not knowing how the relevant module was actually imported makes
    it actually flat out impossible).
    -- https://stackoverflow.com/questions/1436703/what-is-the-difference-between-str-and-repr/1436756#1436756

But what it fundamentally comes down to is this:

1. The docs say that "If at all possible", the `repr` "should look like
   a valid Python expression that could be used to recreate an object with
   the same value (given an appropriate environment)".
2. And only "If this is not possible" should a `<...>` string be returned.

So for our variable `x` of value `int`, this function will return `"int"`
rather than `"<class 'int'>"`.

As another example:

    >>> from typing import Sequence
    >>> Sequence
    typing.Sequence<+T_co>
    >>> Sequence[int]
    typing.Sequence<+T_co>[int]
    >>> repr(Sequence[int])
    'typing.Sequence<+T_co>[int]'
    >>> Sequence[Sequence[int]]
    typing.Sequence<+T_co>[typing.Sequence<+T_co>[int]]
    >>> repr(Sequence[Sequence[int]])
    'typing.Sequence<+T_co>[typing.Sequence<+T_co>[int]]'

We would prefer that `repr(Sequence[int])` returns `"Sequence[int]"`.

Project repo with LICENSE and tests: https://github.com/jboy/argcheck-python3
"""


def _get_repr_that_recreates(x):
    """Return a `repr` string that can be used to re-create its argument."""
    r = repr(x)
    if r.startswith("<class "):
        # The builtin Python `repr` strikes again!
        return x.__name__
    elif "<+T_co>" in r:
        # The `repr` result looks like `"typing.Sequence<+T_co>[int]"`.
        return r.replace("<+T_co>", "")
    else:
        # Otherwise, the result from `repr` is OK.
        return r
