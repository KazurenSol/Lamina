"""
Detect contradictions between newly extracted claims and existing DiscourseState.
V1: exact-text collision check; semantic contradiction detection deferred to CAS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from l_cdea.ingestion.claim_extractor import ExtractedClaim


@dataclass
class ContradictionReport:
    new_claim: str
    existing_claim: str
    source_new: str
    source_existing: str
    severity: str = "potential"


def check_contradictions(
    new_claims: List[ExtractedClaim],
    existing_claims: List[ExtractedClaim],
) -> List[ContradictionReport]:
    """
    Naïve V1 check: flag when two claims from different sources contain the
    same subject-token but opposite polarity ("is" vs "is not").
    """
    reports: List[ContradictionReport] = []
    existing_index = {c.text.lower(): c for c in existing_claims}

    for claim in new_claims:
        negated = claim.text.replace(" is ", " is not ").replace(" can ", " cannot ")
        if negated.lower() in existing_index:
            existing = existing_index[negated.lower()]
            reports.append(ContradictionReport(
                new_claim=claim.text,
                existing_claim=existing.text,
                source_new=claim.source_title,
                source_existing=existing.source_title,
            ))

    return reports
