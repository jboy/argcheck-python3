from abc import ABC, abstractmethod


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
