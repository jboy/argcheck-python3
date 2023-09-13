"""The main implementation of the function argument checking.

Project repo with LICENSE and tests: https://github.com/jboy/argcheck-python3
"""

import functools

from abc import ABC, abstractmethod
from collections import namedtuple
from collections.abc import Sequence as abc_Sequence
from inspect import isclass, signature, Parameter
from typing import Sequence

# Gather round, kids, while grampa tells you a story about the Before Time:
#
# Before Python3.9,
# `typing.Sequence` was a distinct type from `collections.abc.Sequence`:
#  https://docs.python.org/3/library/typing.html#typing.Sequence
#  https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence
#
#       # in file `/usr/lib/python3.5/typing.py`:
#
#       if hasattr(collections_abc, 'Reversible'):
#           class Sequence(Sized, Reversible[T_co], Container[T_co],
#                      extra=collections_abc.Sequence):
#               pass
#       else:
#           class Sequence(Sized, Iterable[T_co], Container[T_co],
#                          extra=collections_abc.Sequence):
#               pass
#
# But from Python3.9 onwards:
# `typing.Sequence` is now merely an alias for `collections.abc.Sequence`:
#
#       # in file `/usr/lib/python3.10/typing.py`:
#
#       Sequence = _alias(collections.abc.Sequence, 1)
#
# Also, before Python3.9,
# `collections.abc.Sequence` didn't support subscripting (`[]`),
# (which is needed to enable a generic alias type in annotations).
# Only `typing.Sequence` supported subscripting:
#
#       >>> import sys; sys.version
#       '3.5.2 (default, Jan 26 2021, 13:30:48) \n[GCC 5.4.0 20160609]'
#       >>> from typing import Sequence as typ_Seq
#       >>> from collections.abc import Sequence as abc_Seq
#       >>> typ_Seq[int]
#       typing.Sequence<+T_co>[int]
#       >>> abc_Seq[int]
#       Traceback (most recent call last):
#             File "<stdin>", line 1, in <module>
#             TypeError: 'ABCMeta' object is not subscriptable
#       >>>
#
# But from Python3.9 onwards:
#
#       >>> import sys; sys.version
#       '3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0]'
#       >>> from typing import Sequence as typ_Seq
#       >>> from collections.abc import Sequence as abc_Seq
#       >>> typ_Seq[int]
#       typing.Sequence[int]
#       >>> abc_Seq[int]
#       collections.abc.Sequence[int]
#       >>>
#
# This code was originally written on Python 3.5, so it uses `typing.Sequence`
# rather than `collections.abc.Sequence` as its "generic Sequence" type.
#
# Also, before Python 3.7,
# you could use `isinstance(value, type)` to check generic types:
#
#       >>> some_list = [1, 2, 3]
#       >>> isinstance(some_list, typ_Seq[int])
#       True
#
# But from Python3.7 onwards:
#
#       >>> some_list = [1, 2, 3]
#       >>> isinstance(some_list, typ_Seq[int])
#       Traceback (most recent call last):
#         File "<stdin>", line 1, in <module>
#         File "/usr/lib/python3.10/typing.py", line 994, in __instancecheck__
#           return self.__subclasscheck__(type(obj))
#         File "/usr/lib/python3.10/typing.py", line 997, in __subclasscheck__
#           raise TypeError("Subscripted generics cannot be used with"
#       TypeError: Subscripted generics cannot be used with class and instance checks
#       >>> isinstance(some_list, abc_Seq[int])
#       Traceback (most recent call last):
#         File "<stdin>", line 1, in <module>
#       TypeError: isinstance() argument 2 cannot be a parameterized generic
#
# Stack Overflow question about this, from someone with the same problem:
#  https://stackoverflow.com/questions/53854463/python-3-7-check-if-type-annotation-is-subclass-of-generic
#
# So this caused the hasty definition of a new class `checks.isTypeOfSequence`
# when I encountered this problem on a deployment to a Python3.10 system!


from .better_repr import _get_repr_that_recreates
from .checks import (_AbstractArgValueCheck,
        isTypeEqualTo, isTypeOfSequence, eachAll)
from .exceptions import (
        _InternalExecutionError, AnnotationCompilationError,
        CallArgBindingRejection, CallArgCheckExecutionError)
from .import_annotated import Annotated, _AnnotatedAlias


class _ObjectWithCtorArgsRepr(ABC):
    """An ABC with a `__repr__()` method that calls a `_ctor_args()` mothed."""
    @abstractmethod
    def _ctor_args(self) -> str:
        pass

    def __repr__(self) -> str:
        return "{self.__class__.__name__}({ctor_args})".format(
                self=self, ctor_args=self._ctor_args())


class _DeclFuncParam(_ObjectWithCtorArgsRepr):
    """Describe a single declared function parameter for exceptions."""
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name

    def _ctor_args(self) -> str:
        return "idx={self.idx}, name={self.name!r}".format(
                self=self)

    def __str__(self) -> str:
        return "[{self.idx}]={self.name!r}".format(
                self=self)


class _FuncCallArg(_ObjectWithCtorArgsRepr):
    """Describe a single function call argument for exceptions."""
    def __init__(self, idx_or_kwd, val):
        self.idx_or_kwd = idx_or_kwd
        self.val = val

    def _ctor_args(self) -> str:
        return "idx_or_kwd={self.idx_or_kwd!r}, val={self.val!r}".format(
                self=self)

    def __str__(self) -> str:
        return "[{self.idx_or_kwd!r}]={self.val!r}".format(
                self=self)


_DeclParamArgChecksPair = \
        namedtuple("_DeclParamArgChecksPair", "decl_param arg_checks")


class _ArgChecksForOneFuncDecl:
    """Construct the argument checks for one decorated function declaration.

    This class performs two tasks for validation of a function declaration:

    1. Extract a list of declared function parameters from the signature.
    2. Evaluate the PEP-484 type hint annotations to construct argument checks.

    Note that this class does NOT actually *check* any function arguments;
    it only constructs lists of argument checks that will be performed at
    a later time (when the decorated function is actually called).
    The actual checking of actual function arguments will be performed by
    an instance of class `_CheckArgsOneFuncCall`.

    There will be one instance of this class constructed per decorated function
    declaration to validate.  All tasks performed by this class are performed
    in its `__init__` function; after this instance initialization is complete,
    no more processing (or internal-state manipulation) occurs in the instance.

    This instance construction occurs when the decorator `validate_call`
    is executed, rather than when the decorated function itself is called.
    In addition to front-loading the computation at module-loading time,
    this also enables us to pre-check the validity of our specified validity
    checks (!), rather than discovering any errors at some later "runtime"
    (when the decorated function is actually called for the first time). :P

    The function signature returned by stdlib function ``inspect.signature``:
     https://docs.python.org/3/library/inspect.html#introspecting-callables-with-the-signature-object
    describes function parameters using the stdlib type ``inspect.Parameter``:
     https://github.com/python/cpython/blob/3.11/Lib/inspect.py#L2654

    We will borrow and store these same instances of ``inspect.Parameter`` in
    this class; the stdlib type already includes slots, so we can be confident
    that the memory usage is minimal and the attribute access is efficient.

    Once we've extracted a list of elements of ``inspect.Parameter``, we will
    traverse the PEP-484 type hint annotations to construct argument checks:
     https://peps.python.org/pep-0484/

    In this package, we recognise the PEP-593 ``Annotated[T, metadata]`` type:
     https://peps.python.org/pep-0593/

    So for each parameter where there is a PEP-484 type hint annotation, this
    type annotation might form a graph of nested ``Annotated[T, metadata]``
    that must be traversed.
    """
    __slots__ = ("_func_name", "_signature", "_arg_checks_for_params",)

    def __init__(self, func):
        # If we validate multiple functions, we probably want to know which one
        # has experienced an error...
        func_name = func.__name__
        self._func_name = func_name

        # Standard library function `inspect.signature` exists since Python3.3:
        #  https://docs.python.org/3/library/inspect.html#introspecting-callables-with-the-signature-object
        self._signature = signature(func)

        _NoAnnot = Parameter.empty
        # Calculate a sequence of `(decl_param, arg_check)` pairs;
        # then convert to a tuple for immutability.
        #
        # Note: Originally, I instead converted to an `OrderedDict` for both
        # in-order iteration and dict lookup.  But then Python complained
        # (via a terse TypeError message `TypeError: unhashable type: 'list'`)
        # that there's a list-valued attribute within `inspect.Parameter`, so
        # it can't be hashed, so it can't be used as the key in a dictionary.
        # So now we just use a tuple of pairs.
        self._arg_checks_for_params = tuple([
                _DeclParamArgChecksPair(
                        param,
                        # Evaluate the PEP-484 type-hint annotation if provided.
                        (_eval_PEP_484_param_annot(
                                func_name,
                                param_idx,
                                param_name,
                                param.annotation)
                        if param.annotation is not _NoAnnot
                        # Else (if no annotation provided), an empty tuple.
                        else ())
                )
                for param_idx, (param_name, param)
                in enumerate(self._signature.parameters.items())
        ])

    def check_args_one_call(self, pos_args, kwd_args):
        """Check the arguments passed in a single function call."""
        # Standard library function `inspect.Signature.bind` simulates the
        # result of mapping positional and keyword arguments to parameters:
        #  https://docs.python.org/3/library/inspect.html#inspect.Signature.bind
        #
        # It checks that the number of positional arguments matches the number
        # of positional-or-keyword parameters, checks the validity of keywords,
        # etc.  If there's a problem, a `TypeError` is raised.  If the mapping
        # succeeds, it returns an instance of `inspect.BoundArguments`:
        #  https://docs.python.org/3/library/inspect.html#inspect.BoundArguments
        #  https://docs.python.org/3/library/inspect.html#inspect.BoundArguments.apply_defaults
        try:
            bound_args = self._signature.bind(*pos_args, **kwd_args)
            bound_args.apply_defaults()
        except TypeError as e:
            raise CallArgBindingRejection(e.args) from e

        # Now we need to iterate through:
        # - the annotated argument-checks for the parameters
        # - the function-call arguments that have been mapped to parameters;
        # and match them up.
        #
        # Observation #1:
        # When you declare a function as having multiple keyword parameters,
        # you can specify the keyword arguments in any order.  But then when
        # you map the arguments to parameters using `inspect.Signature.bind`,
        # the bound keyword arguments will be listed in the order of parameter
        # declaration in the `BoundArguments` object:
        #
        #   >>> def kwd_func(a=5, b=7): print((a, b))
        #   ... 
        #   >>> inspect.signature(kwd_func).bind(b=77, a=55).arguments
        #   OrderedDict([('a', 55), ('b', 77)])
        #
        # Observation #2:
        # And when you bind the arguments of a function call to parameters,
        # all bound arguments that you've provided are listed in the order
        # of parameter declaration in the `BoundArguments` object.  And
        # then if you execute method `inspect.BoundArguments.apply_defaults`,
        # *ALL* parameters will be listed in the order of declaration,
        # regardless of whether a non-default argument was supplied or not.
        #
        #   >>> def f7(a, b, *c, d=7, e=8, f=9, **k):
        #   ...     print((a, b, c, d, e, f, g))
        #   ... 
        #   >>> ba7 = inspect.signature(f7).bind(101, 102, f=99, d=77)
        #   >>> ba7.arguments
        #   OrderedDict([('a', 101), ('b', 102), ('d', 77), ('f', 99)])
        #   >>> ba7.apply_defaults()
        #   >>> ba7.arguments
        #   OrderedDict([('a', 101), ('b', 102), ('c', ()),
        #           ('d', 77), ('e', 8), ('f', 99), ('g', {})])
        #
        # So for any given function call, every bound-to parameter listed
        # in the `BoundArguments` object should align to the corresponding
        # declared parameter (in `self._arg_checks_for_params`) if you
        # zip the two ordered containers and iterate over them together.
        # [Don't forget that you can't index into an `OrderedDict`!]
        #
        # UPDATE: Alas, in Python3.9, `BoundArguments.arguments` is a `dict`
        # rather than an `OrderedDict`.  So all of the above reasoning about
        # iteration-by-parameter through ordered containers is now irrelevant.
        # So instead we'll just iterate over `self._arg_checks_for_params` and
        # perform dict-lookups into `BoundArguments.arguments` by `param.name`.
        bound_arguments = bound_args.arguments
        for param_idx, (decl_param, arg_checks_for_param) in \
                enumerate(self._arg_checks_for_params):
            param_name = decl_param.name
            bound_arg = bound_arguments[param_name]

            # Don't forget that hypothetical parameters `*args` & `**kwargs`
            # might have multiple arguments bound to them.
            #
            # Recall that there are 5 "kinds" of parameter
            # according to `inspect.signature`:
            #  https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind
            #
            # - `POSITIONAL_ONLY`
            #     - accepts only positional argument
            #
            # - `POSITIONAL_OR_KEYWORD`
            #     - accepts either positional or keyword argument
            #
            # - `VAR_POSITIONAL`
            #     - a tuple of `*args` (unbound positional arguments)
            #
            # - `KEYWORD_ONLY`
            #     - accepts only keyword argument
            #
            # - `VAR_KEYWORD`
            #     - a dict of `**kwargs` (unbound keyword arguments)
            #
            # We can also work out whether the argument to a given parameter
            # was *actually* passed as a positional argument or a keyword
            # argument by searching for that parameter name in `kwd_args`.
            # This is useful for logging purposes: whether a parameter of
            # kind `POSITIONAL_OR_KEYWORD` ultimately received a positional
            # argument or a keyword argument.
            decl_kind = decl_param.kind
            if decl_kind == decl_param.VAR_KEYWORD:
                # So `bound_arg` will actually be a dict of keyword arguments.
                for kw, kv in bound_arg.items():
                    self._check_one_param_one_arg(
                            param_idx, decl_param, arg_checks_for_param,
                            arg_kwd=kw, bound_arg=kv)
            elif decl_kind == decl_param.VAR_POSITIONAL:
                # So `bound_arg` will actually be a tuple of arguments.
                for a in bound_arg:
                    self._check_one_param_one_arg(
                            param_idx, decl_param, arg_checks_for_param,
                            arg_kwd=None, bound_arg=a)
            else:
                # The parameter kind is either positional or keyword
                # (`POSITIONAL_ONLY`, `POSITIONAL_OR_KEYWORD`, `KEYWORD_ONLY`):
                # always only a single bound argument for this parameter.
                #
                # As noted above, parameters of kind `POSITIONAL_OR_KEYWORD`
                # can receive either a positional or keyword argument; and
                # the only way to work out which happened, is to look for that
                # keyword in `kwd_args`.
                arg_kwd = (param_name if (param_name in kwd_args) else None)
                self._check_one_param_one_arg(
                        param_idx, decl_param, arg_checks_for_param,
                        arg_kwd=arg_kwd, bound_arg=bound_arg)

    def _check_one_param_one_arg(self,
            param_idx, decl_param, arg_checks_for_param, *,
            arg_kwd, bound_arg):
        """Check one argument (either positional or keyword) to one parameter.

        Multi-argument parameters like `*args` & `**kwargs` have already been
        detected in the parent function; the iteration over multiple arguments
        has already occurred.

        Most of the parameters of this function should be self-explanatory.
        Probably the only one that might need some explanation is `arg_kwd`:
        This is the keyword with which an argument was passed, if an argument
        was passed by keyword (otherwise, `None` should be passed instead).
        This keyword is normally the same as the parameter name; but for the
        multi-argument parameter `**kwargs`, each individual keyword will be
        passed here, rather than just the name of the collating parameter
        (normally `**kwargs`).
        """
        for check in arg_checks_for_param:
            try:
                is_valid = check.is_valid(bound_arg)
                if is_valid == True:
                    # Yay, no failures to report.
                    continue
                else:
                    # Uh-oh, there was a failure.
                    # Did the checking code return `False`
                    # or a `dict` of extra context?
                    context_dict = (is_valid if is_valid else {})
                    arg_idx_or_kwd = (arg_kwd if arg_kwd is not None
                            else param_idx)
                    raise check.to_raise_on_failed_check(
                            _DeclFuncParam(
                                    param_idx,
                                    decl_param.name),
                            _FuncCallArg(
                                    arg_idx_or_kwd,
                                    bound_arg),
                            **context_dict)
            except _InternalExecutionError as e:
                arg_idx_or_kwd = (arg_kwd if arg_kwd is not None
                        else param_idx)
                raise CallArgCheckExecutionError(
                        _DeclFuncParam(
                                param_idx,
                                decl_param.name),
                        _FuncCallArg(
                                arg_idx_or_kwd,
                                bound_arg),
                        check,
                        e.operation_that_failed,
                        e.value_that_caused_failure) from None


def _eval_PEP_484_param_annot(func_name, param_idx, param_name, annot):
    """Evaluate the PEP-484 / PEP-593 type-hint annotation for a parameter.

    It is assumed that the value of `annot` is not ``Parameter.empty``.

    The function return-value will be a tuple of `_AbstractCheck`.
    (This tuple detail is important to remember, because recursion may occur.
    This recursive function is responsible for ensuring that it does not return
    a nested result, such as a tuples-of-tuples or lists-of-lists.)

    The function parameters `param_idx` & `param_name` of this function are
    just for error reporting.
    """
    # Graph-recursive case: the annotation is an `Annotated[type, metadata]`
    # (which will actually be an instance of type `_AnnotatedAlias`).
    if isinstance(annot, _AnnotatedAlias):
        type_part = annot.__origin__
        # In class `_AnnotatedAlias`, `self.__metadata__` is a tuple.
        metadata_part = annot.__metadata__
        # Now `metadata_part` is a tuple.
        assert isinstance(metadata_part, tuple)

        # NOTE: The `type` part in `Annotated[type, metadata]` could *also* be
        # an `Annotated[type, metadata]` (and so on, recursively).
        #
        # Recall that our functions `_eval_PEP_484_param_annot` &
        # `_eval_metadata_tuple` will (must) each always return a tuple
        # of values of `_AbstractCheck`.
        #
        # This recursive function is responsible for ensuring that it does not
        # create a nested result (such as a tuples-of-tuples or lists-of-lists)
        # given non-nested values of `type_to_check` & `metadata_to_check`.
        type_to_check = _eval_PEP_484_param_annot(
                func_name, param_idx, param_name, type_part)
        metadata_to_check = _eval_metadata_tuple(
                func_name, param_idx, param_name, metadata_part)
        assert isinstance(type_to_check, tuple)
        assert isinstance(metadata_to_check, tuple)
        # "Adding" two tuples concatenates them, thus maintaining the invariant
        # that the function should not return nested tuples-of-tuples.
        return type_to_check + metadata_to_check

    elif hasattr(annot, "__origin__") and (
            annot.__origin__ in (Sequence, abc_Sequence)):
        # It's `typing.Sequence`, a "generic" class type.
        # We want to type-check its nested generic type argument.
        # It appears that the `typing` module checks the number of arguments
        # to `Sequence` and complains if there's more or less than one.
        assert hasattr(annot, "__args__")
        assert len(annot.__args__) == 1
        check_for_nested_type = _eval_PEP_484_param_annot(
                func_name, param_idx, param_name, annot.__args__[0])
        # Now we want to wrap this check in an `eachAll`.
        return (isTypeOfSequence(annot), eachAll(check_for_nested_type[0]))

    # Base case of recursion: the annotation is simply a type
    # (such as `int`, which is a value of type `<class 'type'>`).
    elif isclass(annot):
        return (isTypeEqualTo(annot),)

    else:
        # Otherwise, it's something else.  What is it?
        raise AnnotationCompilationError(
                _DeclFuncParam(
                        param_idx,
                        param_name),
                annot,
                "unrecognised PEP-484 / PEP-593 type-hint annotation")


def _eval_metadata_tuple(func_name, param_idx, param_name, metadata_tuple):
    """Evaluate the PEP-593 ``Annotated`` metadata tuple for a parameter.

    These eval'd metadata are used for value checks (rather than type checks).

    The function return-value will be a tuple of `_AbstractArgValueCheck`.
    (This tuple detail is important to remember, because recursion may occur.
    This recursive function is responsible for ensuring that it does not return
    a nested result, such as a tuples-of-tuples or lists-of-lists.)

    The function parameters `param_idx` & `param_name` of this function are
    just for error reporting.
    """
    # In class `_AnnotatedAlias`, `self.__metadata__` is a tuple.
    # This is why we expect `metadata_tuple` to be a tuple.
    # But in our own usage of `Annotated[type, metadata]`,
    # we also allow aggregation of metadata using Python list syntax.
    # This is why we also allow `metadata_tuple` to be a list.
    if not isinstance(metadata_tuple, (tuple, list)):
        raise AnnotationCompilationError(
                _DeclFuncParam(
                        param_idx,
                        param_name),
                str(metadata_tuple),
                "expected a metadata tuple or list; received type `%s`" %
                        _get_repr_that_recreates(type(metadata_tuple)))

    # Evaluate each metadata tuple element in turn; return a tuple.
    # (I would obviously prefer to use a list comprehension for this;
    # but this function must ensure that it does not create or return
    # a nested result, such as a tuples-of-tuples or lists-of-lists.
    # Thus, it cannot simply comprehend a sequence of elements into a list,
    # in case one of the elements contains its own nested tuple or list.)
    result = []
    for m in metadata_tuple:
        one_metadata_to_check = _eval_one_metadata_value(
                func_name, param_idx, param_name, m)
        if isinstance(one_metadata_to_check, (list, tuple)):
            # Yup, here's a nested list or tuple.
            # => We need to "flatten" it, by extending rather than appending.
            result.extend(one_metadata_to_check)
        else:
            result.append(one_metadata_to_check)
    return tuple(result)


def _eval_one_metadata_value(
        func_name, param_idx, param_name, one_metadata_value):
    """Evaluate just one PEP-593 ``Annotated`` metadata value for a parameter.

    These eval'd metadata are used for value checks (rather than type checks).

    The function return-value may be any of: a list of, a tuple of, or single
    value of `_AbstractArgValueCheck`.

    (This tuple detail is important to remember, because recursion may occur.
    This recursive function is responsible for ensuring that it does not return
    a nested result, such as a tuples-of-tuples or lists-of-lists.)

    The function parameters `param_idx` & `param_name` of this function are
    just for error reporting.
    """
    if isinstance(one_metadata_value, (list, tuple)):
        # OK, eval each metadata element in turn; return a tuple.
        return _eval_metadata_tuple(
                func_name, param_idx, param_name, one_metadata_value)
    # Otherwise, is it an (unconstructed) type?
    elif isinstance(one_metadata_value, _AbstractArgValueCheck):
        # It's an already-constructed instance of a _AbstractArgValueCheck.
        # We don't need to construct this --- just return it.
        return one_metadata_value
    elif isclass(one_metadata_value):
        # It's a class...
        if issubclass(one_metadata_value, _AbstractArgValueCheck):
            # It's an unconstructed type of a _AbstractArgValueCheck.
            # Let's construct an instance of this type.
            return one_metadata_value()
        else:
            # Otherwise, it's some other unconstructed type.
            # What kind of type is this?
            raise AnnotationCompilationError(
                    _DeclFuncParam(
                            param_idx,
                            param_name),
                    one_metadata_value,
                    "expected a value-check class; received type `%s`" %
                            _get_repr_that_recreates(type(one_metadata_value)))
    else:
        # Otherwise, it's something else.  What is it?
        raise AnnotationCompilationError(
                _DeclFuncParam(
                        param_idx,
                        param_name),
                one_metadata_value,
                "expected a value-check instance; received value of type `%s`" %
                        _get_repr_that_recreates(type(one_metadata_value)))


def validate_call(func: callable) -> callable:
    #print(func.__annotations__)
    arg_checks_for_one_decl = _ArgChecksForOneFuncDecl(func)

    @functools.wraps(func)
    def wrap_func_for_validation(*pos_args, **kwd_args):
        #print("Calling wrapped func: %s" % signature(func).parameters)
        #print("pos_args = %s" % str(pos_args))
        #print("kwd_args = %s" % str(kwd_args))
        arg_checks_for_one_decl.check_args_one_call(pos_args, kwd_args)
        return func(*pos_args, **kwd_args)

    #print(signature(wrap_func_for_validation))
    return wrap_func_for_validation
