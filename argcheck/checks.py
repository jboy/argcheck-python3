"""A catalogue of classes for function argument checks.

Project repo with LICENSE and tests: https://github.com/jboy/argcheck-python3
"""

import inspect as _inspect

from abc import ABC, abstractmethod
from collections import namedtuple

from .better_repr import _get_repr_that_recreates
from .exceptions import (_InternalExecutionError,
        AnnotationConstructionError)
from .exceptions import *


class _AbstractCheck(ABC):
    """Abstract base class for all function argument checks."""
    @abstractmethod
    def is_valid(self, x) -> bool:
        pass

    @abstractmethod
    def to_raise_on_failed_check(self, param, arg) -> Exception:
        pass

    def _ctor_args(self) -> str:
        return ""

    def __repr__(self) -> str:
        return "{self.__class__.__name__}({ctor_args})".format(
                self=self, ctor_args=self._ctor_args())

    def __str__(self) -> str:
        return "{self.__class__.__name__}".format(
                self=self)


class _AbstractTypeCheck(_AbstractCheck):
    """Abstract base class for checks of declared parameter type."""
    def __init__(self, type_declared):
        self.type_declared = type_declared

    def to_raise_on_failed_check(self, param, arg) -> Exception:
        arg_received = arg.val
        return CallArgTypeCheckViolation(param, arg, self,
                self.type_declared, type(arg_received))

    def _type_declared(self) -> str:
        return "{self.type_declared.__name__}".format(
                self=self)

    def _ctor_args(self) -> str:
        return "type_declared={type_declared}".format(
                self=self, type_declared=self._type_declared())

    def __str__(self) -> str:
        return "{self.__class__.__name__} for type {type_declared}".format(
                self=self, type_declared=self._type_declared())


class isTypeEqualTo(_AbstractTypeCheck):
    """Check whether the argument type is equal to the declared type."""
    def __init__(self, type_declared):
        super().__init__(type_declared)

    def is_valid(self, x) -> bool:
        return isinstance(x, self.type_declared)


class isTypeOfSequence(_AbstractTypeCheck):
    """Check whether the argument type is of a sequence type."""
    def __init__(self, type_declared):
        super().__init__(type_declared)

    def is_valid(self, x) -> bool:
        # Before Python3.7, this test was very easy:
        # You could use `isinstance(value, type)` to check generic types:
        #       >>> import typing
        #       >>> some_list = [1, 2, 3]
        #       >>> isinstance(some_list, typing.Sequence[int])
        #       True
        #
        # But from Python3.7 onwards, this no longer works. :(
        # [Read the long comment at the start of `argcheck/impl.py`
        # for the full error message in all its glory.]
        # And here's a Stack Overflow question about this,
        # from someone with the same problem:
        #  https://stackoverflow.com/questions/53854463/python-3-7-check-if-type-annotation-is-subclass-of-generic
        #
        # So now we use duck-typing, to check for the following attributes
        # that are listed for `collections.abc.Sequence`:
        #  https://docs.python.org/3/library/collections.abc.html
        #
        #   - `__getitem__`
        #   - `__len__`
        #   - `__contains__`
        #   - `__iter__`
        #   - `__reversed__`
        #   - `index`
        #   - `count`
        #
        # As you would hope/expect, this accepts `list` and rejects `dict`.
        # Note: This rejects both `str` and `tuple`, neither of which have
        # attribute `__reversed__`:
        #
        #       >>> hasattr("", '__reversed__')
        #       False
        #       >>> hasattr((), '__reversed__')
        #       False
        #
        # Both `typing.Sequence` and `collections.abc.Sequence` define the
        # `Sequence` type as `Reversible`, so this must be intentional:
        #  https://docs.python.org/3/library/typing.html#typing.Sequence
        #  https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes
        #
        # Oh well, sorry `str` and `tuple`.  We'll never forget that magic time
        # when you were `isinstance(x, typing.Sequence)` in Python3.5!
        #
        #       >>> isinstance("", typing.Sequence)
        #       True
        #       >>> isinstance((), typing.Sequence)
        #       True
        #
        return (hasattr(x, '__getitem__') and hasattr(x, '__len__') and
                hasattr(x, '__contains__') and hasattr(x, '__iter__') and
                hasattr(x, '__reversed__') and
                hasattr(x, 'index') and hasattr(x, 'count'))


class _AbstractArgValueCheck(_AbstractCheck):
    """Abstract base class for checks of argument value preconditions."""
    def to_raise_on_failed_check(self, param, arg) -> Exception:
        return CallArgValueCheckViolation(param, arg, self)


class isNotEmpty(_AbstractArgValueCheck):
    """Check whether a container of values is NOT empty."""
    def is_valid(self, x) -> bool:
        try:
            return len(x) > 0
        except (AttributeError, TypeError, ValueError) as e:
            # If we can't calculate the length, then the type is wrong.
            raise _InternalExecutionError("len(x)", x)


class isMonotonicIncr(_AbstractArgValueCheck):
    """Check whether the values in a sequence are monotonic increasing."""
    def is_valid(self, x) -> bool:
        num_elems = None
        # First, can we calculate the length?
        try:
            num_elems = len(x)
        except (AttributeError, TypeError, ValueError) as e:
            # If we can't calculate the length, then the type is wrong.
            raise _InternalExecutionError("len(x)", x)

        # Second, can we perform pairwise comparisons?
        if num_elems <= 1:
            # There are not enough elements to make any pairwise comparisons.
            # If the sequence contains a single element, then we'll consider
            # it to be a valid monotonic-increasing sequence.
            # And then for continuity, we'll declare that an empty sequence
            # is also monotonic-increasing.
            return True
        num_pairwise_comparisons = num_elems - 1
        # The following code would be simpler with Numpy arrays :P
        try:
            return all((x[i+1:] > x[i:-1])
                    for i in range(num_pairwise_comparisons))
        except (AttributeError, TypeError, ValueError) as e:
            # If we can't calculate the length, then the type is wrong.
            raise _InternalExecutionError("x[i+1] > x[i]", x)


class isPositive(_AbstractArgValueCheck):
    """Check whether a value is positive."""
    def is_valid(self, x) -> bool:
        try:
            return x > 0
        except (AttributeError, TypeError, ValueError) as e:
            # If we can't perform a `>` comparison, then the type is wrong.
            raise _InternalExecutionError("x > 0", x)


CallingLocation = namedtuple("CallingLocation", "file_name line_num")


def _get_calling_location():
    frame = _inspect.currentframe()
    # Verify that this implementation provides Python stack frame support.
    #  https://docs.python.org/3/library/inspect.html#inspect.currentframe
    assert frame is not None

    # The filename of this module.
    this_filename =  frame.f_code.co_filename

    while frame is not None and frame.f_code.co_filename == this_filename:
        frame = frame.f_back

    # If we exited that while-loop, either we left this module,
    # or we ran out of frames (which shouldn't happen).
    assert frame is not None
    # If we got to here, then we definitely left this module.
    # Return the filename & line-num of the code immediately outside.
    return CallingLocation(frame.f_code.co_filename, frame.f_lineno)


class _AbstractEachCheck(_AbstractArgValueCheck):
    """Abstract base class for checks applied to each element in a sequence."""
    def __init__(self, check_applied_to_each):
        # Because `eachAll` is constructed using `(...)` rather than `[...]`,
        # this function will not receive an Abstract Syntax Tree that it can
        # traverse, but will instead receive a pre-constructed instance of
        # type `eachAll`.
        #
        # When the client code constructs `eachAll`, it can supply either
        # a type or an instantiated value of that type.  If the client
        # supplied a type, we must construct an instance of that type
        # (assuming no arguments are required by the constructor).
        if isinstance(check_applied_to_each, _AbstractCheck):
            self.check_applied_to_each = check_applied_to_each
        elif issubclass(check_applied_to_each, _AbstractCheck):
            self.check_applied_to_each = check_applied_to_each()
        else:
            raise AnnotationConstructionError(
                    type(self),
                    _get_calling_location(),
                    "expected an `_AbstractCheck` instance; received value: %s" % (
                            _get_repr_that_recreates(check_applied_to_each)))


    def to_raise_on_failed_check(self, param, arg, **kwargs) -> Exception:
        idx_within_sequence = kwargs["idx_within_sequence"]
        value_within_sequence = kwargs["value_within_sequence"]
        return CallArgEachCheckViolation(param, arg, self,
                idx_within_sequence, value_within_sequence)

    def _ctor_args(self) -> str:
        check = _get_repr_that_recreates(self.check_applied_to_each)
        return "check_applied_to_each={check}".format(
                check=check)

    def __str__(self) -> str:
        check = _get_repr_that_recreates(self.check_applied_to_each)
        return "{self.__class__.__name__}({check})".format(
                self=self, check=check)


class eachAll(_AbstractEachCheck):
    """Apply the check to each element in a sequence; require all to return True."""
    def __init__(self, check_applied_to_each):
        super().__init__(check_applied_to_each)

    def is_valid(self, x) -> bool:
        check_applied_to_each = self.check_applied_to_each
        try:
            for idx, elem in enumerate(x):
                if not check_applied_to_each.is_valid(elem):
                    return dict(
                            idx_within_sequence=idx,
                            value_within_sequence=elem)
        except (AttributeError, TypeError, ValueError) as e:
            # If we can't perform a for-loop, then the type is wrong.
            raise _InternalExecutionError("for elem in x", x)

        # Otherwise, no failures...
        return True
