class DiscourseError(Exception):
    pass


class DiscourseImportError(DiscourseError):
    pass


class SalienceError(DiscourseError):
    pass


class MemoryGraphError(DiscourseError):
    pass


class PersistenceError(DiscourseError):
    pass


class SchemaVersionError(PersistenceError):
    pass


class ProvenanceError(DiscourseError):
    pass
