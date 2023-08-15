import random


class TestCase:
    """A single test-case to run."""
    def __init__(self, descr, func, pos_args, kwd_args, expected):
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


class ExpectedReturn:
    """How to calculate what return-value to expect from the test-function.

    To verify that argument-passing and value-returning work properly
    (without getting too complicated), every test-function will return
    the value of the argument passed to its first declared parameter
    (if the test-function declares any parameters at all).

    This is complicated slightly by functions that declare no parameters.
    The solution to this is easy enough: The function will return `None`.

    It's complicated slightly more by default values, because a function
    can never know whether a parameter's value was passed in by a caller
    or is the declared default value for that parameter.

    Ironically, we can't simply `inspect` the test-function signature
    (which is, after all, the basis of the functionality of `argcheck`)
    because the test-function is likely to be wrapped by a decorator that
    has its own signature.

    So we must look at the test-function signature ourselves, and hard-code
    whatever return-value we expect (to be received in `expected_value`).

    But if it's the simple case (where we are definitely passing an argument
    into the first declared parameter of the test function), we can instead
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
            return ("expected return-value supplied as positional argument %d" %
                    self.arg_idx_or_kwd)
        elif isinstance(self.arg_idx_or_kwd, str):
            return ("expected return-value supplied as keyword argument %s" %
                    repr(self.arg_idx_or_kwd))
        else:
            return ("expected return-value %s" % repr(self.expected_value))


class ExpectedException:
    """We expect the test-function to raise the specified exception."""
    def __init__(self, ex_type, ex_repr, ex_str):
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
        return ("expected exception %s" % self.ex_repr)


def get_random_int():
    """Return a random integer in the range [-1000, 1000]."""
    return random.randint(-1000, 1000)

