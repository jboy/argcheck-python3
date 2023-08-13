"""A simple, minimalist stand-in for ``typing.Annotated`` for Python < 3.9."""

try:
    # The following import will fail if you're running Python < 3.9:
    #  https://docs.python.org/3/library/typing.html#typing.Annotated
    from typing import Annotated, _AnnotatedAlias
    # Also, special methods `__class_getitem__` was added in Python 3.7,
    # to implement PEP 560:
    #  https://peps.python.org/pep-0560/

except ImportError as e:

    class _TypeOfAnnotated:
        """An extremely simple, minimalist stand-in for `typing.Annotated`.

        This stand-in class is useful if you're running Python < 3.9.

        This code is copied from the Python library implementation:
         https://github.com/python/cpython/blob/3.11/Lib/typing.py
        """
        __slots__ = ()

        def __eq__(self, other):
            return isinstance(other, _TypeOfAnnotated)

        def __getitem__(self, params):
            if not isinstance(params, tuple) or len(params) < 2:
                raise TypeError("Annotated[...] should be used "
                                "with at least two arguments (a type and an "
                                "annotation).")
            # If we copy-paste the body of `_type_check`, then we also
            # need to copy-paste several other type definitions...
            #msg = "Annotated[t, ...]: t must be a type."
            #origin = _type_check(params[0], msg, allow_special_forms=True)
            origin = params[0]
            metadata = tuple(params[1:])  #  NOTE: `metadata` is now a tuple.
            return _AnnotatedAlias(origin, metadata)


    Annotated = _TypeOfAnnotated()


    class _AnnotatedAlias:
        """Runtime representation of an annotated type.

        At its core 'Annotated[t, dec1, dec2, ...]' is an alias for the type 't'
        with extra annotations. The alias behaves like a normal typing alias.
        Instantiating is the same as instantiating the underlying type; binding
        it to types is also the same.

        The metadata itself is stored in a '__metadata__' attribute as a tuple.

        This stand-in class is useful if you're running Python < 3.9.

        This code is copied from the Python library implementation:
         https://github.com/python/cpython/blob/3.11/Lib/typing.py
        """

        def __init__(self, origin, metadata):
            if isinstance(origin, _AnnotatedAlias):
                metadata = origin.__metadata__ + metadata
                origin = origin.__origin__
            self.__origin__ = origin
            self.__metadata__ = metadata

        def __repr__(self):
            return "typing.Annotated[{}, {}]".format(
                _type_repr(self.__origin__),
                ", ".join(repr(a) for a in self.__metadata__)
            )


    def _type_repr(obj):
        """Return the repr() of an object, special-casing types (internal helper).

        If obj is a type, we return a shorter version than the default
        type.__repr__, based on the module and qualified name, which is
        typically enough to uniquely identify a type.  For everything
        else, we fall back on repr(obj).
        """
        if isinstance(obj, type):
            if obj.__module__ == 'builtins':
                return obj.__qualname__
            return '{obj.__module__}.{obj.__qualname__}'.format(obj=obj)
        if obj is ...:
            return('...')
        if isinstance(obj, types.FunctionType):
            return obj.__name__
        return repr(obj)
