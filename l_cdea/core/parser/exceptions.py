class ParserError(Exception):
    pass


class TokenizationError(ParserError):
    pass


class LexingError(ParserError):
    pass


class StructureError(ParserError):
    pass
