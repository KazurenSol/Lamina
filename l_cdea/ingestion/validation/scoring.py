"""
compute_score(value) → float in [0.0, 1.0]

Weighted combination of:
  - Provenance confidence       (70 %)
  - Source type reliability     (20 %)  dataset > execution > document
  - Structural completeness     (10 %)  optional provenance fields filled

Confidence MUST NOT be random; all inputs are deterministic.
"""
from __future__ import annotations

from l_cdea.discourse.provenance.model import ProvenancedValue

# Source-type reliability weights (dataset most reliable)
_SOURCE_TYPE_WEIGHT: dict = {
    "dataset":   1.0,
    "execution": 0.8,
    "document":  0.6,
}

_CONFIDENCE_WEIGHT   = 0.70
_SOURCE_WEIGHT       = 0.20
_COMPLETENESS_WEIGHT = 0.10


def compute_score(value: ProvenancedValue, mode: str = "document") -> float:
    """Deterministic quality score for a ProvenancedValue."""
    prov = value.provenance

    confidence = max(0.0, min(1.0, prov.confidence))

    source_weight = _SOURCE_TYPE_WEIGHT.get(prov.source_type, 0.5)

    # Count optional fields that are filled
    filled = sum([
        prov.source_path is not None,
        prov.chunk_id is not None,
        prov.location is not None,
    ])
    completeness = filled / 3.0

    # Dictionary mode: raise confidence weight for document-sourced definitions
    # so short high-quality entries clear the REJECT_THRESHOLD.
    conf_weight = _CONFIDENCE_WEIGHT
    if (mode == "dictionary"
            and prov.source_type == "document"
            and prov.extraction_method in ("definition_extractor", "pattern_v1")):
        from l_cdea.ingestion.modes.config import get_mode_config
        override = get_mode_config(mode).confidence_weight_override
        if override is not None:
            conf_weight = override

    score = (
        conf_weight          * confidence
        + _SOURCE_WEIGHT     * source_weight
        + _COMPLETENESS_WEIGHT * completeness
    )
    return min(1.0, max(0.0, score))
