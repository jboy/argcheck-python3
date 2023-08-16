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
        run_all_tests, get_random_int)

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


if __name__ == "__main__":
    run_all_tests(_TEST_CASES)
