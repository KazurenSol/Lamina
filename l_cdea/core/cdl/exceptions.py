class CDLError(Exception):
    """Base CDL exception."""


class InvalidOperatorError(CDLError):
    pass


class GraphExecutionError(CDLError):
    pass


class TypeMismatchError(CDLError):
    pass
