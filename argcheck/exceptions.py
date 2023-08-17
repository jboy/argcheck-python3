"""Exception classes to report errors relating to function argument checking.

These exception classes are defined in an "extends" inheritence hierarchy.
The hierarchy is arranged from non-specific (the base) to the most-specific.
Child classes add attributes to their parents to encapsulate more-specific
information that is available.  [The raising of a non-specific exception is
considered sub-optimal.  We prefer to raise more-specific, more-descriptive
exceptions that provide more information for debugging.]

The existence of the non-specific & less-specific exceptions in the hierarchy
is intended to enable polymorphic handling of raised exceptions by client code.
Client code can choose a level of specificity at which it handles exceptions,
for a trade-off between convenience (base classes) vs detail (child classes).

The hierarchy of classes has been designed to respect Liskov substitutability.
[This was not difficult, as each class possesses only 3 methods: ``__init__``,
a valid ``__repr__``, and a convenient ``str__``.  The implicit RTTI (RunTime
Type Information) of Python's `except` construct takes care of the rest.]

Note that attributes are not the only determiner of the inheritence hierarchy.
Exception/error conditions that have different "meanings" will be represented
by distinct classes (and possibly even distinct branches of the hierarchy),
even if these classes happen to contain the same attributes.

The base class of the exception hierarchy is class `ArgCheckException`
(which inherits from Python's builtin ``Exception``).

This module uses the following class-name suffices to differentiate exceptions
of different high-level category:

- ``-Exception``
- ``-CompilationError`` (e.g., class `AnnotationCompilationError`)
- ``-Rejection`` (e.g., class `CallArgBindingRejection`)
- ``-ExecutionError``
- ``-Violation``

At the highest level:

- ``-Exception``: This expresses a non-specific exception.  [As already noted,
  the raising of a non-specific ``-Exception`` is considered sub-optimal.
  We prefer to use more-specific, more-descriptive exceptions that provide
  more information for debugging.]

As the decorator is executed to "compile" type-annotations into checks:

- ``-CompilationError``: This indicates that a failure occurred during
  the "annotation compilation" phase; this failure prevented successful
  compilation.

When the decorated function is called explicitly:

- ``-Rejection``: This indicates that error-checking in Python stdlib code
  successfully detected a problem in the function-call arguments (such as
  an incorrect number of function-call arguments) and refused to proceed.

- ``-ExecutionError``: This indicates that a code execution error occurred
  during argument checking.  [Such errors generally implicate insufficient
  coverage by the specified argument checks:  Some argument check has made
  some implicit assumptions about the argument value that it has received
  --- assumptions that should instead have been encoded as explicit argument
  checks that were executed earlier in the queue of argument checks.]

- ``-Violation``:
  This indicates that an argument check has successfully detected that a
  function-call argument violates a declared function parameter pre-condition.

In summary: The ``-Rejection`` and ``-Violation`` exception types indicate
that this validation code has successfully detected invalid function-call
arguments.  In contrast, the ``-ExecutionError`` exception types indicate that
some function-call arguments have caused the execution of the argument checks
to fail in unintended ways.

This is the current exception hierarchy:

    `ArgCheckException`
            |-- `_InternalExecutionError`
            |-- `AnnotationCompilationError`
            |-- `AnnotationConstructionError`
            |-- `CallArgBindingRejection`
            |-- `CallArgCheckException`
                        |-- `CallArgCheckExecutionError`
                        |-- `CallArgCheckViolation`
                                    |-- `CallArgTypeCheckViolation`
                                    |-- `CallArgValueCheckViolation`
                                    |-- `CallArgEachCheckViolation`


Aside: In this module (and in fact, in this whole ``argcheck`` package), when
we talk about "parameters" (frequently shortened to ``Param``), we are talking
about **function parameters** rather than **neural-network parameters**.

Project repo with LICENSE and tests: https://github.com/jboy/argcheck-python3
"""

import inspect as _inspect
from .better_repr import _get_repr_that_recreates


def _get_parent_func_params(num_parent_steps=1):
    """Return ``(param_names, arg_values)`` of the parent function.

    ``param_names`` & ``arg_values`` will each be of type ``tuple``.

    Important: The parameter names in ``param_names``, and the argument values
    in `arg_values`, should be returned in the order of parameter declaration
    in the function signature.
    """
    frame = _inspect.currentframe()
    # Verify that this implementation provides Python stack frame support.
    #  https://docs.python.org/3/library/inspect.html#inspect.currentframe
    assert frame is not None

    # Walk back a specified number of steps to the desired ancestor frame.
    assert num_parent_steps > 0
    for i in range(num_parent_steps):
        frame = frame.f_back
        # Verify that there is a parent.
        assert frame is not None

    frame_code = frame.f_code
    argcount = frame_code.co_argcount
    varnames = frame_code.co_varnames
    # Verify that all the "variables" are parameters (not other locals).
    assert len(varnames) == argcount

    # Pair off parameter names with parameter values (ie, arguments).
    frame_locals = frame.f_locals
    arg_values = [frame_locals[name] for name in varnames]

    # Avoid creation of any reference cycles, just in case:
    #  https://docs.python.org/3/library/inspect.html#the-interpreter-stack
    del frame

    return (tuple(varnames), tuple(arg_values))


class ArgCheckException(Exception):
    """A non-specific exception during function argument checking."""
    def _init_attrs_from_locals(self):
        """Initialise the attributes of the current class from init parameters.

        Each derived class `__init__` method will call this method,
        to initialise the attributes specific to that derived class.

        This method does NOT initialise attributes of parent or child classes:
        Those parent or child classes will invoke this method themselves
        from their own `__init__` methods, to initialise their own attributes,
        using the following method call:

            self._init_attrs_from_locals()

        The intention of this code is for our exceptions to be something like
        "namedtuple + ('extends'-style inheritence of namedtuple attributes) +
        (dynamic polymorphism of the resulting exception types)".

        Also, DRY ("Don't Repeat Yourself") for attribute initialisation and
        auto-generated `__repr__` methods.
        """
        (param_names, arg_values) = _get_parent_func_params(num_parent_steps=2)
        # Verify that the parameters appear to be the parameters of a method.
        assert param_names[0] == "self"

        # Store all parameter names *after* the "self" parameter.
        ctor_param_names = param_names[1:]
        ctor_arg_values = arg_values[1:]

        self._ctor_param_names = ctor_param_names
        for param_name, arg_value in zip(ctor_param_names, ctor_arg_values):
            assert param_name != "_ctor_param_names"  # reserved for our use!
            # It doesn't matter if we overwrite an existing (identical) value.
            setattr(self, param_name, arg_value)

    def __init__(self):
        super().__init__()
        self._init_attrs_from_locals()

    def __repr__(self) -> str:
        """This ``__repr__`` method works for all descendants of this class."""
        class_name = self.__class__.__name__
        get_repr = _get_repr_that_recreates
        ctor_kwd_args = ", ".join(
                "%s=%s" % (
                        param_name,
                        get_repr(getattr(self, param_name))
                )
                for param_name in self._ctor_param_names)
        return "%s(%s)" % (class_name, ctor_kwd_args)

    def __str__(self) -> str:
        """This ``__str__`` method must be re-defined in every descendant."""
        return "exception during function argument check"


class _InternalExecutionError(ArgCheckException):
    """An execution error occurred during an operation to check an argument.

    Think of this as a ``TypeError``/``ValueError``/``AttributeError` that
    contains 2 named attributes:

    - the operation that failed
    - the value that caused the failure.

    This exception type is intended for internal use (in argcheck code) only:
    A raised exception of this type should be caught and translated to one of
    the public exception types before it leaves the argcheck codespace.

    Nevertheless, this exception type inherits from class `ArgCheckException`
    just to ensure that external code can still catch all argcheck exceptions
    using class `ArgCheckException`.
    """
    def __init__(self, operation_that_failed, value_that_caused_failure):
        super().__init__()
        self._init_attrs_from_locals()

    def __str__(self) -> str:
        return "operation `{self.operation_that_failed!s}` failed for this value: {self.value_that_caused_failure!r}".format(
                self=self)


class AnnotationCompilationError(ArgCheckException):
    """Unable to compile a function parameter type annotation into checks."""
    def __init__(self, param, annotation, problem):
        super().__init__()
        self._init_attrs_from_locals()

    def __str__(self):
        return "unable to compile type annotation `{self.annotation!s}` into checks: {self.problem!s}".format(
                self=self)


class AnnotationConstructionError(ArgCheckException):
    """Unable to construct a check at module-loading time."""
    def __init__(self, check_type, calling_location, problem):
        super().__init__()
        self._init_attrs_from_locals()

    def __str__(self):
        check_type = _get_repr_that_recreates(self.check_type)
        file_name = self.calling_location.file_name
        line_num = self.calling_location.line_num
        return "unable to construct check `{check_type!s}` at `{file_name!s}:{line_num!s}` due to invalid constructor argument: {self.problem!s}".format(
                self=self, check_type=check_type, file_name=file_name, line_num=line_num)


class CallArgBindingRejection(ArgCheckException):
    """Unable to bind the arguments of a function call to declared parameters.

    For example, there might have been:
    - missing a required argument
    - too many positional arguments
    - got an unexpected keyword argument

    This is a translation of the ``TypeError`` raised by standard library
    function ``inspect.Signature.bind`` if a binding rejection occurs.
    """
    def __init__(self, exception_args):
        super().__init__()
        self._init_attrs_from_locals()

    def __str__(self):
        args = self.exception_args
        if isinstance(args, tuple) and len(args) == 1:
            # Standard library exceptions such as `TypeError`
            # hold their message string in an attribute `.args`,
            # which (via a setter property) is always a tuple.
            args = args[0]
        return "unable to bind function call argument: {args!r}".format(
                args=args)


class CallArgCheckException(ArgCheckException):
    """A non-specific exception relating to a single function call argument."""
    def __init__(self, param, arg_that_caused_failure):
        super().__init__()
        self._init_attrs_from_locals()

    def __str__(self) -> str:
        return "error for param {self.param!s}: {self.arg_that_caused_failure!r}".format(
                self=self)


class CallArgCheckExecutionError(CallArgCheckException):
    """An execution error occurred during the checking of a precondition."""
    def __init__(self,
            param,
            arg_that_caused_failure,
            during_check,
            operation_that_failed,
            value_that_caused_failure):
        super().__init__(param, arg_that_caused_failure)
        self._init_attrs_from_locals()

    def __str__(self) -> str:
        return "operation `{self.operation_that_failed!s}` failed for param {self.param!s} during check `{self.during_check!r}` for this value: {self.value_that_caused_failure!r}".format(
                self=self)


class CallArgCheckViolation(CallArgCheckException):
    """A function parameter check has detected the violation of a precondition.

    A function parameter check has detected the violation of a precondition
    by a function-call argument value.

    The difference between this class and parent class `CallArgCheckException`
    is that this exception is raised when a function parameter check has been
    successfully computed, but the check determines that a precondition has
    been violated.
    """
    def __init__(self,
            param,
            arg_that_caused_failure,
            check_that_failed):
        super().__init__(param, arg_that_caused_failure)
        self._init_attrs_from_locals()

    def __str__(self) -> str:
        return "violation of check `{self.check_that_failed!r}` for param {self.param!s}: {self.arg_that_caused_failure!r}".format(
                self=self)


class CallArgTypeCheckViolation(CallArgCheckViolation):
    """The declared type of a parameter was violated by the supplied argument."""
    def __init__(self,
            param,
            arg_that_caused_failure,
            check_that_failed,
            type_declared,
            type_received):
        super().__init__(param, arg_that_caused_failure, check_that_failed)
        self._init_attrs_from_locals()

    def __str__(self) -> str:
        type_dec = _get_repr_that_recreates(self.type_declared)
        type_rec = _get_repr_that_recreates(self.type_received)
        return "violation of type check `{self.check_that_failed!r}` for param {self.param!s} (declared={type_dec}; received={type_rec}): {self.arg_that_caused_failure!r}".format(
                self=self, type_dec=type_dec, type_rec=type_rec)


class CallArgValueCheckViolation(CallArgCheckViolation):
    """A value constraint was violated by the supplied function-call argument."""
    def __init__(self,
            param,
            arg_that_caused_failure,
            check_that_failed):
        super().__init__(param, arg_that_caused_failure, check_that_failed)
        self._init_attrs_from_locals()

    def __str__(self) -> str:
        return "violation of value-constraint check `{self.check_that_failed!r}` for param {self.param!s}: {self.arg_that_caused_failure!r}".format(
                self=self)


class CallArgEachCheckViolation(CallArgCheckViolation):
    """A sequence check was violated by the supplied function-call argument."""
    def __init__(self,
            param,
            arg_that_caused_failure,
            check_that_failed,
            idx_within_sequence,
            value_within_sequence):
        super().__init__(param, arg_that_caused_failure, check_that_failed)
        self._init_attrs_from_locals()

    def __str__(self) -> str:
        return "violation of sequence check `{self.check_that_failed!r}` for param {self.param!s}: {self.arg_that_caused_failure!r} (at sequence element [{self.idx_within_sequence!r}]={self.value_within_sequence!r})".format(
                self=self)
