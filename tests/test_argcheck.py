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

from typing import Sequence
from _testing_framework import (TestCase, ExpectedReturn, ExpectedException,
        run_all_tests, get_random_int, get_random_positive_int, get_random_str,
        get_random_list)

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


# NOTE: The following functions are NOT test-cases.  They are merely
# *inputs* to the test-cases: recepients of function-call arguments,
# with or without the `@validate_call` decorator, and with or without
# parameter type annotations, to be invoked and *tested* by test-cases.
#
# Each of these functions may be called by any number of test-cases.
#
# The names of these functions also have no significance (other than
# to be unique and vaguely-descriptive).


# To verify that argument-passing and value-returning work properly
# (without getting too complicated), every test-function should be
# coded so that it returns either:
#   - the argument passed to a specific one of its parameters; or
#   - a hard-coded constant value.
#
# It is preferable for the test-function to return the argument passed
# to one of its parameters (so that the connection between arguments
# and return-values can be verified).
#
# But if a function declares no parameters (and thus, cannot take any
# arguments), the function should return a hard-coded constant value.
#
# Whatever the test-function returns (whether a parameter argument or
# a hard-coded constant value), it should not change.  This enables
# the test-code writer to read the test-function and predict what the
# return-value will be.  The test-case can then be coded accordingly.
#
# By convention, if a parameter argument is returned, the parameter
# returned should be the first declared parameter.  And by convention,
# if a function declares no parameters, it should return `None` as the
# hard-coded constant value.
#
# But neither of these conventions is strictly required, just as long
# as *which* parameter is returned does not change; and as long as the
# value of the constant does not change.


def no_deco_0_params_no_annots():
    return None


def no_deco_1_params_no_annots(p):
    return p


def no_deco_2_params_no_annots(p_1, p_2):
    return p_1


@ac.validate_call
def deco_0_params_no_annots():
    return None


@ac.validate_call
def deco_1_params_no_annots(p):
    return p


@ac.validate_call
def deco_2_params_no_annots(p_1, p_2):
    return p_1


@ac.validate_call
def deco_2_params_annot_1_int(p_1: int, p_2):
    return p_1


@ac.validate_call
def deco_2_params_annot_2_int(p_1, p_2: int):
    return p_1


@ac.validate_call
def deco_1_params_annot_int_dflt_int(p: int = 33):
    return p


@ac.validate_call
def deco_1_params_annot_int_dflt_str(p: int = "hello"):
    return p


class MyClass:
    """A simple non-builtin type."""
    def __init__(self, x):
        self.x = x

    def __repr__(self):
        return "{self.__class__.__name__}({self.x!r})".format(self=self)

    def __str__(self):
        return "{self.x!r}".format(self=self)


@ac.validate_call
def deco_1_params_annot_MyClass(p: MyClass):
    return p


@ac.validate_call
def deco_1_params_annot_int(p: int):
    return p


@ac.validate_call
def deco_1_params_annot_Sequence(p: Sequence):
    return p


@ac.validate_call
def deco_1_params_annot_Sequence_int(p: Sequence[int]):
    return p


@ac.validate_call
def deco_1_params_annot_int_isPositive(p: ac.Annotated[int, ac.isPositive]):
    return p


_TEST_CASES = [
    # TestCase(description,
    TestCase("normal Python (no @validate_call): 0 params, no annots",
            # function to call,
            no_deco_0_params_no_annots,
            # function positional arguments (a tuple),
            (),
            # function keyword arguments (a dict),
            {},
            # expected return-value or expected exception
            ExpectedReturn(arg_idx_or_kwd=None, expected_value=None),
    ),

    TestCase("normal Python (no @validate_call): 1 params, no annots",
            no_deco_1_params_no_annots,
            (get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("normal Python (no @validate_call): 2 params, no annots",
            no_deco_2_params_no_annots,
            (get_random_int(), get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("normal Python (no @validate_call): too few pos-args",
            no_deco_2_params_no_annots,
            (get_random_int(),), {},
            ExpectedException(TypeError,
                    'TypeError("{tc.func.__name__}() missing 1 required positional argument: \'p_2\'",)',
                    "{tc.func.__name__}() missing 1 required positional argument: 'p_2'"),
    ),

    TestCase("normal Python (no @validate_call): too many pos-args",
            no_deco_2_params_no_annots,
            (get_random_int(), get_random_int(), get_random_int(),), {},
            ExpectedException(TypeError,
                    "TypeError('{tc.func.__name__}() takes 2 positional arguments but 3 were given',)",
                    '{tc.func.__name__}() takes 2 positional arguments but 3 were given'),
    ),

    TestCase("normal Python (no @validate_call): undeclared kwd-arg",
            no_deco_1_params_no_annots,
            (get_random_int(),), dict(undeclared_kwd=get_random_int(),),
            ExpectedException(TypeError,
                    'TypeError("{tc.func.__name__}() got an unexpected keyword argument \'undeclared_kwd\'",)',
                    "{tc.func.__name__}() got an unexpected keyword argument 'undeclared_kwd'"),
    ),

    TestCase("@validate_call: 0 params, no annots",
            deco_0_params_no_annots,
            (), {},
            ExpectedReturn(arg_idx_or_kwd=None, expected_value=None),
    ),

    TestCase("@validate_call: 1 params, no annots",
            deco_1_params_no_annots,
            (get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: 2 params, no annots",
            deco_2_params_no_annots,
            (get_random_int(), get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: too few pos-args",
            deco_2_params_no_annots,
            (get_random_int(),), {},
            ExpectedException(ac.exceptions.CallArgBindingRejection,
                    'CallArgBindingRejection(exception_args=("missing a required argument: \'p_2\'",))',
                    'unable to bind function call argument: "missing a required argument: \'p_2\'"'),
    ),

    TestCase("@validate_call: too many pos-args",
            deco_2_params_no_annots,
            (get_random_int(), get_random_int(), get_random_int(),), {},
            ExpectedException(ac.exceptions.CallArgBindingRejection,
                    "CallArgBindingRejection(exception_args=('too many positional arguments',))",
                    "unable to bind function call argument: 'too many positional arguments'"),
    ),

    TestCase("@validate_call: undeclared kwd-arg",
            deco_1_params_no_annots,
            (get_random_int(),), dict(undeclared_kwd=get_random_int(),),
            ExpectedException(ac.exceptions.CallArgBindingRejection,
                    'CallArgBindingRejection(exception_args=("got an unexpected keyword argument \'undeclared_kwd\'",))',
                    'unable to bind function call argument: "got an unexpected keyword argument \'undeclared_kwd\'"'),
    ),

    TestCase("@validate_call: annot params(:int, :), args(:int, :int)",
            deco_2_params_annot_1_int,
            (get_random_int(), get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:int, :), args(:int, :str)",
            deco_2_params_annot_1_int,
            (get_random_int(), get_random_str(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:int, :), args(:str, :int)",
            deco_2_params_annot_1_int,
            (get_random_str(), get_random_int(),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p_1'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
                    "violation of type check `isTypeEqualTo(type_declared=int)` for param [0]='p_1' (declared=int; received=str): _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:, :int), args(:int, :int)",
            deco_2_params_annot_2_int,
            (get_random_int(), get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:, :int), args(:int, :str)",
            deco_2_params_annot_2_int,
            (get_random_int(), get_random_str(),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=1, name='p_2'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=1, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
                    "violation of type check `isTypeEqualTo(type_declared=int)` for param [1]='p_2' (declared=int; received=str): _FuncCallArg(idx_or_kwd=1, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:, :int), args(:str, :int)",
            deco_2_params_annot_2_int,
            (get_random_str(), get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:int = :int), args(:int)",
            deco_1_params_annot_int_dflt_int,
            (get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:int = :int), args()",
            deco_1_params_annot_int_dflt_int,
            (), {},
            ExpectedReturn(arg_idx_or_kwd=None, expected_value=33),
    ),

    TestCase("@validate_call: annot params(:int = :int), args(:str)",
            deco_1_params_annot_int_dflt_int,
            (get_random_str(),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
                    "violation of type check `isTypeEqualTo(type_declared=int)` for param [0]='p' (declared=int; received=str): _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:int = :str), args(:int)",
            deco_1_params_annot_int_dflt_str,
            (get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:int = :str), args()",
            deco_1_params_annot_int_dflt_str,
            (), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val='hello'), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
                    "violation of type check `isTypeEqualTo(type_declared=int)` for param [0]='p' (declared=int; received=str): _FuncCallArg(idx_or_kwd=0, val='hello')"),
    ),

    TestCase("@validate_call: annot params(:int = :str), args(:str)",
            deco_1_params_annot_int_dflt_str,
            (get_random_str(),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=str)",
                    "violation of type check `isTypeEqualTo(type_declared=int)` for param [0]='p' (declared=int; received=str): _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:MyClass), args(:MyClass)",
            deco_1_params_annot_MyClass,
            (MyClass(get_random_int()),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:MyClass), args(:int)",
            deco_1_params_annot_MyClass,
            (get_random_int(),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=MyClass), type_declared=MyClass, type_received=int)",
                    "violation of type check `isTypeEqualTo(type_declared=MyClass)` for param [0]='p' (declared=MyClass; received=int): _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:int), args(:int)",
            deco_1_params_annot_int,
            (get_random_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:int), args(:MyClass)",
            deco_1_params_annot_int,
            (MyClass(get_random_int()),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=int), type_declared=int, type_received=MyClass)",
                    "violation of type check `isTypeEqualTo(type_declared=int)` for param [0]='p' (declared=int; received=MyClass): _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:Sequence), args(:list)",
            deco_1_params_annot_Sequence,
            (get_random_list(get_random_int),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:Sequence), args(:tuple)",
            deco_1_params_annot_Sequence,
            (tuple(get_random_list(get_random_int)),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:Sequence), args(:str)",
            deco_1_params_annot_Sequence,
            (get_random_str(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:Sequence), args(:int)",
            deco_1_params_annot_Sequence,
            (get_random_int(),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=Sequence), type_declared=typing.Sequence, type_received=int)",
                    "violation of type check `isTypeEqualTo(type_declared=Sequence)` for param [0]='p' (declared=typing.Sequence; received=int): _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:Sequence), args(:MyClass)",
            deco_1_params_annot_Sequence,
            (MyClass(get_random_int()),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=Sequence), type_declared=typing.Sequence, type_received=MyClass)",
                    "violation of type check `isTypeEqualTo(type_declared=Sequence)` for param [0]='p' (declared=typing.Sequence; received=MyClass): _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:Sequence[int]), args(:list[int])",
            deco_1_params_annot_Sequence_int,
            (get_random_list(get_random_int),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:Sequence[int]), args(:tuple[int])",
            deco_1_params_annot_Sequence_int,
            (tuple(get_random_list(get_random_int)),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:Sequence[int]), args(:list[str])",
            deco_1_params_annot_Sequence_int,
            (get_random_list(get_random_str,(),dict(min_len=3,max_len=6)),), {},
            ExpectedException(ac.exceptions.CallArgEachCheckViolation,
                    "CallArgEachCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=eachAll(check_applied_to_each=isTypeEqualTo(type_declared=int)), idx_within_sequence=0, value_within_sequence={ex.value_within_sequence!r})",
                    "violation of sequence check `eachAll(check_applied_to_each=isTypeEqualTo(type_declared=int))` for param [0]='p': _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}) (at sequence element [0]={ex.value_within_sequence!r})"),
    ),

    TestCase("@validate_call: annot params(:Sequence[int]), args(:str)",
            deco_1_params_annot_Sequence_int,
            (get_random_str(),), {},
            ExpectedException(ac.exceptions.CallArgEachCheckViolation,
                    "CallArgEachCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=eachAll(check_applied_to_each=isTypeEqualTo(type_declared=int)), idx_within_sequence=0, value_within_sequence={ex.value_within_sequence!r})",
                    "violation of sequence check `eachAll(check_applied_to_each=isTypeEqualTo(type_declared=int))` for param [0]='p': _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}) (at sequence element [0]={ex.value_within_sequence!r})"),
    ),

    TestCase("@validate_call: annot params(:Sequence[int]), args(:int)",
            deco_1_params_annot_Sequence_int,
            (get_random_int(),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=Sequence), type_declared=typing.Sequence[int], type_received=int)",
                    "violation of type check `isTypeEqualTo(type_declared=Sequence)` for param [0]='p' (declared=typing.Sequence[int]; received=int): _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:Sequence[int]), args(:MyClass)",
            deco_1_params_annot_Sequence_int,
            (MyClass(get_random_int()),), {},
            ExpectedException(ac.exceptions.CallArgTypeCheckViolation,
                    "CallArgTypeCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isTypeEqualTo(type_declared=Sequence), type_declared=typing.Sequence[int], type_received=MyClass)",
                    "violation of type check `isTypeEqualTo(type_declared=Sequence)` for param [0]='p' (declared=typing.Sequence[int]; received=MyClass): _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:int>0), args(:int>0)",
            deco_1_params_annot_int_isPositive,
            (get_random_positive_int(),), {},
            ExpectedReturn(arg_idx_or_kwd=0),
    ),

    TestCase("@validate_call: annot params(:int>0), args(:int==0)",
            deco_1_params_annot_int_isPositive,
            (0,), {},
            ExpectedException(ac.exceptions.CallArgValueCheckViolation,
                    "CallArgValueCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isPositive())",
                    "violation of value-constraint check `isPositive()` for param [0]='p': _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

    TestCase("@validate_call: annot params(:int>0), args(:int<0)",
            deco_1_params_annot_int_isPositive,
            (-get_random_positive_int(),), {},
            ExpectedException(ac.exceptions.CallArgValueCheckViolation,
                    "CallArgValueCheckViolation(param=_DeclFuncParam(idx=0, name='p'), arg_that_caused_failure=_FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r}), check_that_failed=isPositive())",
                    "violation of value-constraint check `isPositive()` for param [0]='p': _FuncCallArg(idx_or_kwd=0, val={ex.arg_that_caused_failure.val!r})"),
    ),

]


if __name__ == "__main__":
    run_all_tests(_TEST_CASES, verbose_info=True)
