class MECPError(Exception):
    pass


class CostModelError(MECPError):
    pass


class SchedulingError(MECPError):
    pass


class PruningError(MECPError):
    pass
