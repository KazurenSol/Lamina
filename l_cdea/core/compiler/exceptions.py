class CompilerError(Exception):
    pass


class TypeResolutionError(CompilerError):
    pass


class BindingError(CompilerError):
    pass


class GraphConstructionError(CompilerError):
    pass
