class CanonicalizationError(Exception):
    pass


class EquivalenceDetectionError(CanonicalizationError):
    pass


class NormalizationError(CanonicalizationError):
    pass
