import sys

from inspect import signature
from random import randint
from string import ascii_lowercase
from typing import Sequence


class TestCase:
    """A single test-case to run."""
    def __init__(self, descr, func, pos_args: tuple, kwd_args: dict, expected):
        # Validate the types of the attributes in this TestCase,
        # to ensure that we've hard-coded our tests correctly.
        assert isinstance(descr, str)
        assert hasattr(func, '__call__')
        assert isinstance(pos_args, tuple)
        assert isinstance(kwd_args, dict)
        assert isinstance(expected, (ExpectedReturn, ExpectedException))

        self.descr = descr
        self.func = func
        self.pos_args = pos_args
        self.kwd_args = kwd_args
        self.expected = expected


def run_all_tests(test_cases: Sequence[TestCase], *,
        info_stream=sys.stdout, error_stream=sys.stderr,
        verbose_info=False):
    """Run each test-case in `test_cases` (a Sequence of `TestCase`).

    At the end, return the number of tests that passed.
    """
    for test_idx, test_case in enumerate(test_cases):
        _run_test(test_idx, test_case,
                info_stream=info_stream,
                error_stream=error_stream,
                verbose_info=verbose_info)

    num_tests_passed = len(test_cases)
    if info_stream is not None:
        print("\nAll tests passed: {n} of {n}".format(n=num_tests_passed),
                file=info_stream)

    return num_tests_passed


class ExpectedReturn:
    """How to calculate what return-value to expect from the test-function.

    To verify that argument-passing and value-returning work properly
    (without getting too complicated), every test-function should be
    coded so that it returns either:
      - the argument passed to a specific one of its parameters; or
      - a hard-coded constant value.

    It is preferable for the test-function to return the argument passed
    to one of its parameters (so that the connection between arguments
    and return-values can be verified).

    But if a function declares no parameters (and thus, cannot take any
    arguments), the function should return a hard-coded constant value.

    Whatever the test-function returns (whether a parameter argument or
    a hard-coded constant value), it should not change.  This enables
    the test-code writer to read the test-function and predict what the
    return-value will be.  The test-case can then be coded accordingly.

    By convention, if a parameter argument is returned, the parameter
    returned should be the first declared parameter.  And by convention,
    if a function declares no parameters, it should return `None` as the
    hard-coded constant value.

    But neither of these conventions is strictly required, just as long
    as *which* parameter is returned does not change; and as long as the
    value of the constant does not change.

    If it's the simple case (where we are definitely passing an argument
    into the first declared parameter of the test function), we can simply
    specify `expected_value=Ellipsis`, meaning "It's whatever we supplied."
    """
    def __init__(self, *, arg_idx_or_kwd, expected_value=Ellipsis):
        # Validate the types of the attributes in this ExpectedReturn,
        # to ensure that we've hard-coded our tests correctly.
        assert (arg_idx_or_kwd is None) or isinstance(arg_idx_or_kwd, (int,str))

        # `(arg_idx_or_kwd is None)` means "No arguments were passed."
        # `(expected_value is Ellipsis)` means "Expect the argument we passed."
        #
        # These two conditions cannot both be true at the same time.
        assert not ((arg_idx_or_kwd is None) and (expected_value is Ellipsis))

        # The position-index (if a positional argument was passed)
        # or keyword (if a keyword argument was passed)
        # or `None` (if no arguments were passed to the parameter).
        self.arg_idx_or_kwd = arg_idx_or_kwd
        # Whatever return-value we expect from the test-function:
        # - `Ellipsis` if we expect it to be the argument that we passed; or
        # - some hard-coded value that we deduced by looking at the function.
        self.expected_value = expected_value

    def __repr__(self):
        ctor_args = "arg_idx_or_kwd={self.arg_idx_or_kwd!r}, expected_value={self.expected_value!r}".format(self=self)
        return "{self.__class__.__name__}({ctor_args})".format(
                self=self, ctor_args=ctor_args)

    def __str__(self):
        if isinstance(self.arg_idx_or_kwd, int):
            return ("expected return-value passed as positional argument %d" %
                    self.arg_idx_or_kwd)
        elif isinstance(self.arg_idx_or_kwd, str):
            return ("expected return-value passed as keyword argument %s" %
                    repr(self.arg_idx_or_kwd))
        else:
            return ("expected return-value %s" % repr(self.expected_value))


class ExpectedException:
    """We expect the test-function to raise the specified exception."""
    def __init__(self, ex_type: type, ex_repr: str, ex_str: str):
        # Validate the types of the attributes in this ExpectedException,
        # to ensure that we've hard-coded our tests correctly.
        assert isinstance(ex_type, type)
        assert isinstance(ex_repr, str)
        assert isinstance(ex_str, str)

        self.ex_type = ex_type  # expected `type(exception)`
        self.ex_repr = ex_repr  # expected `repr(exception)`
        self.ex_str = ex_str    # expected `str(exception)`

    def __repr__(self):
        ctor_args = "ex_type={self.ex_type!r}, ex_repr={self.ex_repr!r}, ex_str={self.ex_str!r}".format(self=self)
        return "{self.__class__.__name__}({ctor_args})".format(
                self=self, ctor_args=ctor_args)

    def __str__(self):
        return ("expected exception %s" % self.ex_type.__name__)


def get_random_int():
    """Return a random integer in the range [-1000, 1000]."""
    return randint(-1000, 1000)


def get_random_positive_int():
    """Return a random integer in the range [1, 1000]."""
    return randint(1, 1000)


def get_random_str(*, min_len=5, max_len=10):
    """Return a random-length string of random lowercase letters.

    The string-length arguments to this function specify a closed-closed range:
    `(min_len=5, max_len=10)`

    The use of a closed-closed range is intentionally similar to the arguments
    to function `random.randint`.
    """
    min_letter_idx = 0
    max_letter_idx = len(ascii_lowercase) - 1

    return "".join(
            ascii_lowercase[randint(min_letter_idx, max_letter_idx)]
            for i in range(randint(min_len, max_len)))


def get_random_list(elem_ctor_func,
        pos_args_for_elem_ctors:tuple=(), kwd_args_for_elem_ctors:dict={}, *,
        min_len=1, max_len=6):
    """Return a random-length list of random elements.

    The random elements in the list will be constructed by supplied function
    `elem_ctor_func`, given positional arguments `pos_args_for_elem_ctors`.

    The list-length arguments to this function specify a closed-closed range:
    `(min_len=5, max_len=10)`

    The use of a closed-closed range is intentionally similar to the arguments
    to function `random.randint`.
    """
    return [elem_ctor_func(*pos_args_for_elem_ctors, **kwd_args_for_elem_ctors)
            for i in range(randint(min_len, max_len))]


class YieldIncrInt:
    """Yield an `int` value that increments with each successive call.

    The first value returned can be specified by `start`.

    The amount by which the value increments can be specified by `incr_func`.
    """
    def __init__(self, *, start=0, incr_func=(lambda: 1)):
        self.curr_val = start
        self.incr_func = incr_func

    def __call__(self):
        curr_val = self.curr_val
        self.curr_val += self.incr_func()
        return curr_val


def _run_test(test_idx: int, test_case: TestCase, *,
        info_stream, error_stream, verbose_info=False):
    """Run a single test-case `test_case` (at test-index `test_idx`).

    If the test fails (by raising or returning anything unexpected/incorrect),
    the function `_complain_test_failure` will be called to report the failure.
    """
    expected = test_case.expected
    if info_stream is not None:
        test_summary = "[{idx}] {t.descr}".format(idx=test_idx, t=test_case)
        if isinstance(expected, ExpectedException):
            test_summary += " => expect exception"

        if verbose_info:
            print("\n{ts}\nFunction: {tc.func.__name__}\nFunc-sig: {sig}\nPos-args: {tc.pos_args}\nKwd-args: {tc.kwd_args}\nExpected: {tc.expected}".format(
                    tc=test_case, ts=test_summary, sig=signature(test_case.func)),
                    file=info_stream)
        else:
            print(test_summary, file=info_stream)

    try:
        return_val = test_case.func(*test_case.pos_args, **test_case.kwd_args)

        # No exception was raised.
        # Did we *expect* that no exception was raised?
        # To put it another way:  Did we expect a return-value or an exception?
        if not isinstance(expected, ExpectedReturn):
            _complain_test_failure(test_idx, test_case,
                    complaint="unexpected return value",
                    extra_info=dict(
                            expected=repr(expected),
                            returned=repr(return_val),
                    ),
                    error_stream=error_stream
            )

        # OK, we *were* expecting a return-value rather than an exception.
        # Let's check the return value.
        if isinstance(expected.arg_idx_or_kwd, int):
            # Expected return-value was supplied as a positional argument.
            assert expected.expected_value is Ellipsis
            expected_return_val = test_case.pos_args[expected.arg_idx_or_kwd]
        elif isinstance(expected.arg_idx_or_kwd, str):
            # Expected return-value was supplied as a keyword argument.
            assert expected.expected_value is Ellipsis
            expected_return_val = test_case.kwd_args[expected.arg_idx_or_kwd]
        else:
            assert expected.arg_idx_or_kwd is None
            expected_return_val = expected.expected_value

        if expected_return_val != return_val:
            _complain_test_failure(test_idx, test_case,
                    complaint="incorrect return value",
                    extra_info=dict(
                            expected=expected_return_val,
                            returned=return_val,
                    ),
                    error_stream=error_stream
            )

        if (info_stream is not None) and verbose_info:
                print("Received: {rv!r}".format(rv=return_val),
                        file=info_stream)

    except Exception as e:
        # An exception was raised.
        # Did we *expect* that an exception would be raised?
        if not isinstance(expected, ExpectedException):
            _complain_test_failure(test_idx, test_case,
                    complaint="unexpected exception raised",
                    extra_info=dict(
                            expected=repr(expected),
                            raised=repr(e),
                    ),
                    error_stream=error_stream
            )

        # OK, we *were* expecting an exception rather than a return-value.
        # Let's check the exception (type & message) that was raised.

        if not isinstance(e, expected.ex_type):
            _complain_test_failure(test_idx, test_case,
                    complaint="incorrect exception type raised",
                    extra_info=dict(
                            expected_ex_type=expected.ex_type,
                            raised_ex_type=type(e),
                            raised_ex_repr=repr(e),
                    ),
                    error_stream=error_stream
            )

        # If we got to here, the exception type that was raised, was expected.
        # Now we check the error message, to verify that it's complaining about
        # the expected problem.
        expected_ex_repr = expected.ex_repr
        if "{tc." in expected_ex_repr or "{ex." in expected_ex_repr:
            # It's a format string!
            expected_ex_repr = expected_ex_repr.format(tc=test_case, ex=e)

        if expected_ex_repr != repr(e):
            # Uh-oh... wrong error message.
            _complain_test_failure(test_idx, test_case,
                    complaint="incorrect `repr()` for raised exception",
                    extra_info=dict(
                            expected_ex_repr=expected_ex_repr,
                            raised_ex_repr=repr(e),
                    ),
                    error_stream=error_stream
            )

        expected_ex_str = expected.ex_str
        if "{tc." in expected_ex_str or "{ex." in expected_ex_str:
            # It's a format string!
            expected_ex_str = expected_ex_str.format(tc=test_case, ex=e)

        if expected_ex_str != str(e):
            # Uh-oh... wrong error message.
            _complain_test_failure(test_idx, test_case,
                    complaint="incorrect `str()` for raised exception",
                    extra_info=dict(
                            expected_ex_str=expected_ex_str,
                            raised_ex_str=str(e),
                    ),
                    error_stream=error_stream
            )

        if (info_stream is not None) and verbose_info:
                print("Received: {ex.__class__.__name__!s}".format(ex=e),
                        file=info_stream)


def _complain_test_failure(test_idx: int, test_case: TestCase, *,
        complaint: str, extra_info={}, error_stream=sys.stderr):
    """Complain about the failure of test-case `test_case`.

    State the complaint in `complaint`; provide any extra info in `extra_info`.

    At the end of this function, `_die` will be called to terminate the process.
    """
    msg = "\n{t.__class__.__name__}[{idx}] failed: \"{t.descr}\"\n\nFunction: {t.func.__name__}\nPos-args: {t.pos_args}\nKwd-args: {t.kwd_args}\nExpected: {t.expected}\n\nComplaint: {complaint}\n".format(
            t=test_case, idx=test_idx, complaint=complaint)

    if extra_info:
        msg = "%sExtra info: %s\n" % (msg, extra_info)

    _die(msg, error_stream=error_stream)


def _die(msg: str, *, error_stream=sys.stderr, exit_status=-1):
    """Print supplied message `msg` and terminate the test-script process.

    Just like the `die` function in Perl.
    """
    if error_stream is not None:
        print("%s\nTests aborted." % msg, file=error_stream)
    sys.exit(exit_status)

