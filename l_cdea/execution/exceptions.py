class ExecutionError(Exception):
    pass


class RuntimeEvaluationError(ExecutionError):
    pass


class ResolutionError(ExecutionError):
    pass


class ContextIsolationError(ExecutionError):
    pass


class MECPOrderViolationError(ExecutionError):
    pass
