#!/usr/bin/env python3
#
# Test `argcheck` for a variety of valid & invalid arguments passed to
# functions with annotated parameters.
#
# Usage from this `tests` directory:
#   python3 test_argcheck.py
#
# Usage from the root directory of the repo:
#   python3 tests/test_argcheck.py
#
# [This module contains the awful boilerplate to set up the import path.]
#
# If all the tests run, and nothing is printed on stderr, and the script ends
# with "All tests passed." printed to stdout, then the tests have succeeded.
# If any tests fail, the script will halt immediately, with the error printed
# to stderr.

import os
import sys

from _testing_framework import (TestCase, ExpectedReturn, ExpectedException,
        get_random_int)

# Yay for Python relative imports.  A very popular topic on Stack Overflow!
_TEST_CASES_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_TEST_CASES_DIR)
# We assume that `sys.path[0]` is the current directory; don't change this.
# But we want the parent directory to be checked immediately after.
# If you insert a value at any index in an empty list (even a non-zero index),
# the value is simply appended.  So inserting at index `1` will always be OK;
# no need to check for empty lists or out-of-range indices.
sys.path.insert(1, _PARENT_DIR)
import argcheck as ac


# NOTE: The following functions are NOT test-cases.  They are merely *inputs*
# to the test-cases:  Recepients of function-call arguments, with or without
# the `@validate_call` decorator, with or without parameter type annotations,
# to be invoked and *tested* by the test-cases.
#
# Each of these functions may be called by any number of test-cases.


def no_deco_0_params_no_annots():
    return None


def no_deco_1_params_no_annots(param):
    return param


def no_deco_2_params_no_annots(param_1, param_2):
    return param_1


@ac.validate_call
def deco_0_params_no_annots():
    return None


@ac.validate_call
def deco_1_params_no_annots(param):
    return param


@ac.validate_call
def deco_2_params_no_annots(param_1, param_2):
    return param_1


@ac.validate_call
def deco_2_params_annot_1_int(param_1: int, param_2):
    return param_1


@ac.validate_call
def deco_2_params_annot_2_int(param_1, param_2: int):
    return param_1


@ac.validate_call
def deco_1_params_annot_int_dflt_int(param: int = 33):
    return param


@ac.validate_call
def deco_1_params_annot_int_dflt_str(param: int = "hello"):
    return param


_TEST_CASES = [
    # TestCase(description,
    TestCase("no decorator: 0 params, no annots, 0 pos-args",
            # function to call,
            no_deco_0_params_no_annots,
            # function positional arguments (a tuple),
            (),
            # function keyword arguments (a dict),
            {},
            # expected return-value or expected exception
            ExpectedReturn(arg_idx_or_kwd=None, expected_value=None),
    ),

    TestCase("no decorator: 1 params, no annots, 1 pos-args",
            no_deco_1_params_no_annots,
            (get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("no decorator: 2 params, no annots, 2 pos-args",
            no_deco_2_params_no_annots,
            (get_random_int(), get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("no decorator: 2 params, no annots, too few pos-args (expect exception)",
            no_deco_2_params_no_annots,
            (get_random_int(),), {},
            ExpectedException(TypeError,
                    'TypeError("{TestCase.func.__name__}() missing 1 required positional argument: \'param_2\'",)',
                    "{TestCase.func.__name__}() missing 1 required positional argument: 'param_2'"),
    ),

    TestCase("no decorator: 2 params, no annots, too many pos-args (expect exception)",
            no_deco_2_params_no_annots,
            (get_random_int(), get_random_int(), get_random_int(),), {},
            ExpectedException(TypeError,
                    "TypeError('{TestCase.func.__name__}() takes 2 positional arguments but 3 were given',)",
                    '{TestCase.func.__name__}() takes 2 positional arguments but 3 were given'),
    ),

    TestCase("no decorator: 1 params, no annots, undeclared kwd-arg (expect exception)",
            no_deco_1_params_no_annots,
            (get_random_int(),), dict(undeclared_kwd=get_random_int(),),
            ExpectedException(TypeError,
                    'TypeError("{TestCase.func.__name__}() got an unexpected keyword argument \'undeclared_kwd\'",)',
                    "{TestCase.func.__name__}() got an unexpected keyword argument 'undeclared_kwd'"),
    ),

    TestCase("@validate_call: 0 params, no annots, 0 pos-args",
            deco_0_params_no_annots,
            (), {},
            ExpectedReturn(arg_idx_or_kwd=None, expected_value=None),
    ),

    TestCase("@validate_call: 1 params, no annots, 1 pos-args",
            deco_1_params_no_annots,
            (get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: 2 params, no annots, 2 pos-args",
            deco_2_params_no_annots,
            (get_random_int(), get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: 2 params, no annots, too few pos-args (expect exception)",
            deco_2_params_no_annots,
            (get_random_int(),), {},
            ExpectedException(ac.exceptions.CallArgBindingRejection,
                    'CallArgBindingRejection(exception_args=("missing a required argument: \'param_2\'",))',
                    'unable to bind function call argument: "missing a required argument: \'param_2\'"'),
    ),

    TestCase("@validate_call: 2 params, no annots, too many pos-args (expect exception)",
            deco_2_params_no_annots,
            (get_random_int(), get_random_int(), get_random_int(),), {},
            ExpectedException(ac.exceptions.CallArgBindingRejection,
                    "CallArgBindingRejection(exception_args=('too many positional arguments',))",
                    "unable to bind function call argument: 'too many positional arguments'"),
    ),

    TestCase("@validate_call: 1 params, no annots, undeclared kwd-arg (expect exception)",
            deco_1_params_no_annots,
            (get_random_int(),), dict(undeclared_kwd=get_random_int(),),
            ExpectedException(ac.exceptions.CallArgBindingRejection,
                    'CallArgBindingRejection(exception_args=("got an unexpected keyword argument \'undeclared_kwd\'",))',
                    'unable to bind function call argument: "got an unexpected keyword argument \'undeclared_kwd\'"'),
    ),

    TestCase("@validate_call: 2 params, (param_1: int), args(int, int)",
            deco_2_params_annot_1_int,
            (get_random_int(), get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: 2 params, (param_1: int), args(int, str)",
            deco_2_params_annot_1_int,
            (get_random_int(), "hello",), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: 2 params, (param_1: int), args(str, int) (expect exception)",
            deco_2_params_annot_1_int,
            ("hello", get_random_int(),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(param_idx=0, param_name='param_1'), arg_that_caused_failure=_FuncCallArg(arg_idx_or_kwd=0, arg_val='hello'), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
                    "violation of type check `isTypeEqualTo(type_declared=int)` for param [0]='param_1' (declared=int; received=str): _FuncCallArg(arg_idx_or_kwd=0, arg_val='hello')"),
    ),

    TestCase("@validate_call: 2 params, (param_2: int), args(int, int)",
            deco_2_params_annot_2_int,
            (get_random_int(), get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: 2 params, (param_2: int), args(int, str) (expect exception)",
            deco_2_params_annot_2_int,
            (get_random_int(), "hello",), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(param_idx=1, param_name='param_2'), arg_that_caused_failure=_FuncCallArg(arg_idx_or_kwd=1, arg_val='hello'), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
                    "violation of type check `isTypeEqualTo(type_declared=int)` for param [1]='param_2' (declared=int; received=str): _FuncCallArg(arg_idx_or_kwd=1, arg_val='hello')"),
    ),

    TestCase("@validate_call: 2 params, (param_2: int), args(str, int)",
            deco_2_params_annot_2_int,
            ("hello", get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: 1 params, (param: int = 33), args(int)",
            deco_1_params_annot_int_dflt_int,
            (get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: 1 params, (param: int = 33), args()",
            deco_1_params_annot_int_dflt_int,
            (), {},
            ExpectedReturn(arg_idx_or_kwd=None, expected_value=33),
    ),

    TestCase("@validate_call: 1 params, (param: int = 33), args(str) (expect exception)",
            deco_1_params_annot_int_dflt_int,
            ("hello",), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(param_idx=0, param_name='param'), arg_that_caused_failure=_FuncCallArg(arg_idx_or_kwd=0, arg_val='hello'), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
                    "violation of type check `isTypeEqualTo(type_declared=int)` for param [0]='param' (declared=int; received=str): _FuncCallArg(arg_idx_or_kwd=0, arg_val='hello')"),
    ),

]


def _die(msg):
    """Print supplied message `msg` and terminate the test-script process.

    Just like the `die` function in Perl.
    """
    print("%s\nTests aborted." % msg, file=sys.stderr)
    sys.exit(-1)


def _complain_test_failure(test_idx, test, *, complaint, extra_info={}):
    """Complain about the failure of test `test` (at test-index `test_idx`).

    State the complaint in `complaint`; provide any extra info in `extra_info`.

    At the end of this function, `_die` will be called to terminate the process.
    """
    if extra_info:
        _die("\nTest[%d] failed: \"%s\"\nFunction: %s\nPos args: %s\nKwd args: %s\n\nComplaint: %s\nExtra info: %s\n" %
                (test_idx, test.descr, test.func.__name__,
                        test.pos_args, test.kwd_args,
                        complaint, extra_info))
    else:
        _die("\nTest[%d] failed: \"%s\"\nFunction: %s\nPos args: %s\nKwd args: %s\n\nComplaint: %s\n" %
                (test_idx, test.descr, test.func.__name__,
                        test.pos_args, test.kwd_args,
                        complaint))


def _run_test(test_idx, test_case):
    """Run a single test-case `test_case` (at test-index `test_idx`).

    If the test fails (by raising or returning anything unexpected/incorrect),
    the function `_complain_test_failure` will be called to report the failure.
    """
    print("[%d] %s" % (test_idx, test_case.descr))
    try:
        return_val = test_case.func(*test_case.pos_args, **test_case.kwd_args)

        # No exception was raised.
        # Did we *expect* that no exception was raised?
        # To put it another way:  Did we expect a return-value or an exception?
        expected = test_case.expected
        if not isinstance(expected, ExpectedReturn):
            _complain_test_failure(test_idx, test_case,
                    complaint="unexpected return value",
                    extra_info=dict(
                            expected=repr(expected),
                            returned=repr(return_val),
                    )
            )

        # OK, we *were* expecting a return-value rather than an exception.
        # Let's check the return value.
        #
        # To verify that argument-passing and value-returning work properly
        # (without getting too complicated), every test-function will return
        # the value of the argument passed to its first declared parameter
        # (if the test-function declares any parameters at all).
        #
        # This is complicated slightly by functions that declare no parameters.
        # The solution to this is easy enough: The function will return `None`.
        #
        # It's complicated slightly more by default values, because a function
        # can never know whether a parameter's value was passed in by a caller
        # or is the declared default value for that parameter.
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
                    )
            )

    except Exception as e:
        # An exception was raised.
        # Did we *expect* that an exception would be raised?
        expected = test_case.expected
        if not isinstance(expected, ExpectedException):
            _complain_test_failure(test_idx, test_case,
                    complaint="unexpected exception raised",
                    extra_info=dict(
                            expected=repr(expected),
                            raised=repr(e),
                    )
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
                    )
            )

        # If we got to here, the exception type that was raised, was expected.
        # Now we check the error message, to verify that it's complaining about
        # the expected problem.
        expected_ex_repr = expected.ex_repr
        if "{TestCase." in expected_ex_repr:
            # It's a format string!
            expected_ex_repr = expected_ex_repr.format(TestCase=test_case)

        if expected_ex_repr != repr(e):
            # Uh-oh... wrong error message.
            _complain_test_failure(test_idx, test_case,
                    complaint="incorrect `repr()` for raised exception",
                    extra_info=dict(
                            expected_ex_repr=expected_ex_repr,
                            raised_ex_repr=repr(e),
                    )
            )

        expected_ex_str = expected.ex_str
        if "{TestCase." in expected_ex_str:
            # It's a format string!
            expected_ex_str = expected_ex_str.format(TestCase=test_case)

        if expected_ex_str != str(e):
            # Uh-oh... wrong error message.
            _complain_test_failure(test_idx, test_case,
                    complaint="incorrect `str()` for raised exception",
                    extra_info=dict(
                            expected_ex_str=expected_ex_str,
                            raised_ex_str=str(e),
                    )
            )


def _run_all_tests():
    """Run each test-case in `_TEST_CASES` (a list of `TestCase`)."""
    for test_idx, test_case in enumerate(_TEST_CASES):
        _run_test(test_idx, test_case)

    print("All tests passed: {n} of {n}".format(n=len(_TEST_CASES)))


if __name__ == "__main__":
    _run_all_tests()
