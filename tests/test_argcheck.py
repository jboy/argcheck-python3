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

from collections import namedtuple
from utils_for_tests import get_random_int

# Yay for Python relative imports.  A very popular topic on Stack Overflow!
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_TESTS_DIR)
# We assume that `sys.path[0]` is the current directory; don't change this.
# But we want the parent directory to be checked immediately after.
# If you insert a value at any index in an empty list (even a non-zero index),
# the value is simply appended.  So inserting at index `1` will always be OK;
# no need to check for empty lists or out-of-range indices.
sys.path.insert(1, _PARENT_DIR)
import argcheck as ac


def valid_no_deco_0_params_no_annots():
    pass


def valid_no_deco_1_params_no_annots(param):
    return param


def valid_no_deco_2_params_no_annots(param_1, param_2):
    return param_1


@ac.validate_call
def valid_deco_0_params_no_annots():
    pass


@ac.validate_call
def valid_deco_1_params_no_annots(param):
    return param


@ac.validate_call
def valid_deco_2_params_no_annots(param_1, param_2):
    return param_1


@ac.validate_call
def valid_deco_2_params_int_annot_1(param_1: int, param_2):
    return param_1


@ac.validate_call
def valid_deco_2_params_int_annot_2(param_1, param_2: int):
    return param_1


@ac.validate_call
def valid_deco_2_params_int_annot_1_2(param_1: int, param_2: int):
    return param_1


Test = namedtuple("Test", "descr func pos_args kwd_args ex_type ex_repr ex_str")

_TESTS = [
    # Test(description,
    Test("normal Python (no deco): 0 params, no annots, 0 pos-args",
            # function to call,
            valid_no_deco_0_params_no_annots,
            # function positional arguments (a tuple),
            (),
            # function keyword arguments (a dict),
            {},
            # expected exception type,
            None,
            # expected `repr(exception)`
            None,
            # expected `str(exception)`
            None),

    Test("normal Python (no deco): 1 params, no annots, 1 pos-args",
            valid_no_deco_1_params_no_annots,
            (get_random_int(),), {},
            None, None, None),

    Test("normal Python (no deco): 2 params, no annots, 2 pos-args",
            valid_no_deco_2_params_no_annots,
            (get_random_int(), get_random_int(),), {},
            None, None, None),

    Test("normal Python (no deco): 2 params, no annots, too few pos-args",
            valid_no_deco_2_params_no_annots,
            (get_random_int(),), {},
            TypeError,
            'TypeError("{test.func.__name__}() missing 1 required positional argument: \'param_2\'",)',
            "{test.func.__name__}() missing 1 required positional argument: 'param_2'",
    ),

    Test("normal Python (no deco): 2 params, no annots, too many pos-args",
            valid_no_deco_2_params_no_annots,
            (get_random_int(), get_random_int(), get_random_int(),), {},
            TypeError,
            "TypeError('{test.func.__name__}() takes 2 positional arguments but 3 were given',)",
            '{test.func.__name__}() takes 2 positional arguments but 3 were given',
    ),

    Test("normal Python (no deco): 1 params, no annots, undeclared kwd-arg",
            valid_no_deco_1_params_no_annots,
            (get_random_int(),),
            dict(undeclared_kwd=get_random_int(),),
            TypeError,
            'TypeError("{test.func.__name__}() got an unexpected keyword argument \'undeclared_kwd\'",)',
            "{test.func.__name__}() got an unexpected keyword argument 'undeclared_kwd'",
    ),

    Test("@validate_call: 0 params, no annots, 0 pos-args",
            valid_deco_0_params_no_annots,
            (), {},
            None, None, None),

    Test("@validate_call: 1 params, no annots, 1 pos-args",
            valid_deco_1_params_no_annots,
            (get_random_int(),), {},
            None, None, None),

    Test("@validate_call: 2 params, no annots, 2 pos-args",
            valid_deco_2_params_no_annots,
            (get_random_int(), get_random_int(),), {},
            None, None, None),

    Test("@validate_call: 2 params, no annots, too few pos-args",
            valid_deco_2_params_no_annots,
            (get_random_int(),), {},
            ac.exceptions.CallArgBindingRejection,
            'CallArgBindingRejection(exception_args=("missing a required argument: \'param_2\'",))',
            'unable to bind function call argument: "missing a required argument: \'param_2\'"',
    ),

    Test("@validate_call: 2 params, no annots, too many pos-args",
            valid_deco_2_params_no_annots,
            (get_random_int(), get_random_int(), get_random_int(),), {},
            ac.exceptions.CallArgBindingRejection,
            "CallArgBindingRejection(exception_args=('too many positional arguments',))",
            "unable to bind function call argument: 'too many positional arguments'",
    ),

    Test("@validate_call: 1 params, no annots, undeclared kwd-arg",
            valid_deco_1_params_no_annots,
            (get_random_int(),),
            dict(undeclared_kwd=get_random_int(),),
            ac.exceptions.CallArgBindingRejection,
            'CallArgBindingRejection(exception_args=("got an unexpected keyword argument \'undeclared_kwd\'",))',
            'unable to bind function call argument: "got an unexpected keyword argument \'undeclared_kwd\'"',
    ),

    Test("@validate_call: 2 params, int annot on param 1, pos args (int, int)",
            valid_deco_2_params_int_annot_1,
            (get_random_int(), get_random_int(),), {},
            None, None, None),

    Test("@validate_call: 2 params, int annot on param 1, pos args (int, str)",
            valid_deco_2_params_int_annot_1,
            (get_random_int(), "hello",), {},
            None, None, None),

    Test("@validate_call: 2 params, int annot on param 1, pos args (str, int)",
            valid_deco_2_params_int_annot_1,
            ("hello", get_random_int(),), {},
            ac.exceptions.CallArgTypeCheckViolation,
            "CallArgTypeCheckViolation(param=_DeclFuncParam(param_idx=0, param_name='param_1'), arg_that_caused_failure=_FuncCallArg(arg_idx_or_kwd=0, arg_val='hello'), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
            "violation of type check `isTypeEqualTo(type_declared=int)` for param [0]='param_1' (declared=int; received=str): _FuncCallArg(arg_idx_or_kwd=0, arg_val='hello')",
    ),

    Test("@validate_call: 2 params, int annot on param 2, pos args (int, int)",
            valid_deco_2_params_int_annot_2,
            (get_random_int(), get_random_int(),), {},
            None, None, None),

    Test("@validate_call: 2 params, int annot on param 2, pos args (int, str)",
            valid_deco_2_params_int_annot_2,
            (get_random_int(), "hello",), {},
            ac.exceptions.CallArgTypeCheckViolation,
            "CallArgTypeCheckViolation(param=_DeclFuncParam(param_idx=1, param_name='param_2'), arg_that_caused_failure=_FuncCallArg(arg_idx_or_kwd=1, arg_val='hello'), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
            "violation of type check `isTypeEqualTo(type_declared=int)` for param [1]='param_2' (declared=int; received=str): _FuncCallArg(arg_idx_or_kwd=1, arg_val='hello')",
    ),

    Test("@validate_call: 2 params, int annot on param 2, pos args (str, int)",
            valid_deco_2_params_int_annot_2,
            ("hello", get_random_int(),), {},
            None, None, None),

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


def _run_test(test_idx, test):
    """Run a single test `test` (at test-index `test_idx`).

    If the test fails (by raising or returning anything unexpected/incorrect),
    the function `_complain_test_failure` will be called to report tho failure.
    """
    print("[%d] %s" % (test_idx, test.descr))

    # Validate the types of the attribute values in this test,
    # to ensure that we've actually hard-coded this test correctly.
    assert isinstance(test.descr, str)
    assert isinstance(test.pos_args, tuple)
    assert isinstance(test.kwd_args, dict)
    assert isinstance(test.ex_type, type) or test.ex_type is None
    assert isinstance(test.ex_repr, str) or test.ex_repr is None
    assert isinstance(test.ex_str, str) or test.ex_str is None

    # To verify that return values work properly, all test functions will
    # return the first positional argument (if supplied); else `None`.
    expect_return_val = (test.pos_args[0] if test.pos_args else None)

    try:
        return_val = test.func(*test.pos_args, **test.kwd_args)

        # No exception was raised.
        # Let's check the test-function return value.
        if ((expect_return_val is None and return_val is not None) or
            (expect_return_val is not None and return_val != expect_return_val)):
                _complain_test_failure(test_idx, test,
                        complaint="incorrect return value",
                        extra_info=dict(
                                expected=expect_return_val,
                                received=return_val,
                        )
                )

    except Exception as e:
        # An exception was raised.
        # However, that might be exactly what this test expects...
        expect_ex_type = test.ex_type
        if test.ex_type is None:
            # Nope, an exception was NOT expected.
            _complain_test_failure(test_idx, test,
                    complaint="unexpected exception raised",
                    extra_info=dict(
                            raised_ex_type=type(e),
                            raised_ex_repr=repr(e),
                    )
            )
        if not isinstance(e, test.ex_type):
            # An exception was NOT expected... but not this exception type!
            _complain_test_failure(test_idx, test,
                    complaint="incorrect exception type raised",
                    extra_info=dict(
                            expected_ex_type=test.ex_type,
                            raised_ex_type=type(e),
                            raised_ex_repr=repr(e),
                    )
            )

        # If we got to here, the exception type that was raised, was expected.
        # Now we check the error message, to verify that it's complaining about
        # the correct problem.
        expect_ex_repr = test.ex_repr
        if (expect_ex_repr is not None) and ("{test." in expect_ex_repr):
            # It's a format string!
            expect_ex_repr = expect_ex_repr.format(test=test)

        if expect_ex_repr != repr(e):
            # Uh-oh... wrong error message.
            _complain_test_failure(test_idx, test,
                    complaint="incorrect `repr()` for raised exception",
                    extra_info=dict(
                            expected_ex_repr=expect_ex_repr,
                            raised_ex_repr=repr(e),
                    )
            )

        expect_ex_str = test.ex_str
        if (expect_ex_str is not None) and ("{test." in expect_ex_str):
            # It's a format string!
            expect_ex_str = expect_ex_str.format(test=test)

        if expect_ex_str != str(e):
            # Uh-oh... wrong error message.
            _complain_test_failure(test_idx, test,
                    complaint="incorrect `str()` for raised exception",
                    extra_info=dict(
                            expected_ex_str=expect_ex_str,
                            raised_ex_str=str(e),
                    )
            )


def _run_all_tests():
    """Run each test in module-variable list `_TESTS` (a list of `Test`)."""
    for test_idx, test in enumerate(_TESTS):
        _run_test(test_idx, test)

    print("All tests passed: {n} of {n}".format(n=len(_TESTS)))


if __name__ == "__main__":
    _run_all_tests()
