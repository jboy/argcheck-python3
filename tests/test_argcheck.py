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


Test = namedtuple("Test", "descr func pos_args kwd_args ex_type ex_repr ex_str")

_TESTS = [
    # Test(description,
    Test("normal Python (no decorator): 0 params, no annots, 0 pos-args",
            # function to call,
            valid_no_deco_0_params_no_annots,
            # function positional arguments (a tuple),
            (),
            # function keyword arguments (a dict),
            {},
            # expected exception type,
            None,
            # expected `str(exception)`
            None,
            # expected `repr(exception)`
            None),

    Test("normal Python (no decorator): 1 params, no annots, 1 pos-args",
            valid_no_deco_1_params_no_annots,
            (get_random_int(),), {},
            None, None, None),

    Test("normal Python (no decorator): 2 params, no annots, 2 pos-args",
            valid_no_deco_2_params_no_annots,
            (get_random_int(), get_random_int()), {},
            None, None, None),

    Test("with decorator: 0 params, no annots, 0 pos-args",
            valid_deco_0_params_no_annots,
            (), {},
            None, None, None),

    Test("with decorator: 1 params, no annots, 1 pos-args",
            valid_deco_1_params_no_annots,
            (get_random_int(),), {},
            None, None, None),

    Test("with decorator: 2 params, no annots, 2 pos-args",
            valid_deco_2_params_no_annots,
            (get_random_int(), get_random_int()), {},
            None, None, None),

]


def _die(msg):
    print("%s\nTests aborted." % msg, file=sys.stderr)
    sys.exit(-1)


def _complain_test_failure(test_idx, test, complaint, extra_info={}):
    if extra_info:
        _die("\nTest[%d] failed: \"%s\"\nFunction: %s\nPos args: %s\nKwd args: %s\n\nComplaint: %s\nExtra info: %s" %
                (test_idx, test.descr, test.func.__name__,
                        test.pos_args, test.kwd_args,
                        complaint, extra_info))
    else:
        _die("\nTest[%d] failed: \"%s\"\nFunction: %s\nPos args: %s\nKwd args: %s\n\nComplaint: %s" %
                (test_idx, test.descr, test.func.__name__,
                        test.pos_args, test.kwd_args,
                        complaint))


def _run_test(test_idx, test):
    print("[%d] %s" % (test_idx, test.descr))

    # To verify that return values work properly, all test functions will
    # return the first positional argument (if supplied); else `None`.
    expect_return_val = (test.pos_args[0] if test.pos_args else None)

    return_val = test.func(*test.pos_args, **test.kwd_args)

    if ((expect_return_val is None and return_val is not None) or
        (expect_return_val is not None and return_val != expect_return_val)):
            _complain_test_failure(test_idx, test,
                    "incorrect return value",
                    extra_info=dict(
                            expected=expect_return_val,
                            received=return_val,
            ))


def _run_all_tests():
    for test_idx, test in enumerate(_TESTS):
        _run_test(test_idx, test)

    print("All tests passed: {n} of {n}".format(n=len(_TESTS)))


if __name__ == "__main__":
    _run_all_tests()
