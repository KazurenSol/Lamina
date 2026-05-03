"""
L-CDEA data module — deterministic data-backed operator support.

Importing this module registers all built-in V1 datasets.
"""
from l_cdea.data.datasets import Dataset, DatasetRecord
from l_cdea.data.registry import (
    DatasetRegistry,
    register_dataset, get_dataset, list_datasets, has_dataset,
    DatasetConflictError, DatasetNotFoundError,
)
from l_cdea.data.loaders import from_dict, from_json_file
from l_cdea.data.lookup import (
    lookup, contains, is_miss,
    DataLookupTrace,
    get_last_lookup_trace, get_all_lookup_traces, clear_lookup_trace,
    LOOKUP_MISS_PREFIX,
)
from l_cdea.data.validation import validate_dataset, assert_valid
from l_cdea.core.types.base import SemanticType

# ── Built-in geography datasets ────────────────────────────────────────────────

_GEO_PROVENANCE = {"source": "l_cdea_builtin", "domain": "geography", "curator": "L-CDEA V1"}

_country_capitals = from_dict(
    name="country_capitals_v1",
    domain="geography",
    key_type=SemanticType.ENTITY,
    value_type=SemanticType.ENTITY,
    records={
        "France":         "Paris",
        "Spain":          "Madrid",
        "Japan":          "Tokyo",
        "United States":  "Washington, D.C.",
        "Mexico":         "Mexico City",
        "Canada":         "Ottawa",
        "Germany":        "Berlin",
        "Italy":          "Rome",
        "United Kingdom": "London",
        "China":          "Beijing",
    },
    version="1.0.0",
    provenance=_GEO_PROVENANCE,
)

_us_state_capitals = from_dict(
    name="us_state_capitals_v1",
    domain="geography",
    key_type=SemanticType.ENTITY,
    value_type=SemanticType.ENTITY,
    records={
        "Texas":          "Austin",
        "California":     "Sacramento",
        "Florida":        "Tallahassee",
        "New York":       "Albany",
        "North Carolina": "Raleigh",
        "Virginia":       "Richmond",
        "Washington":     "Olympia",
        "Arizona":        "Phoenix",
        "Alaska":         "Juneau",
        "Hawaii":         "Honolulu",
    },
    version="1.0.0",
    provenance=_GEO_PROVENANCE,
)

register_dataset(_country_capitals)
register_dataset(_us_state_capitals)


__all__ = [
    "Dataset",
    "DatasetRecord",
    "DatasetRegistry",
    "register_dataset",
    "get_dataset",
    "list_datasets",
    "has_dataset",
    "DatasetConflictError",
    "DatasetNotFoundError",
    "from_dict",
    "from_json_file",
    "lookup",
    "contains",
    "is_miss",
    "DataLookupTrace",
    "get_last_lookup_trace",
    "get_all_lookup_traces",
    "clear_lookup_trace",
    "LOOKUP_MISS_PREFIX",
    "validate_dataset",
    "assert_valid",
]
