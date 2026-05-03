"""
Registry of validated adaptation proposals awaiting manual approval.
Proposals MUST NOT be auto-registered. Human approval required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AdaptationProposal:
    name: str
    version: str
    type: str           # "encoding", "compression", "algorithm"
    description: str
    validation_report_ref: str
    benchmark_report_ref: str
    approved: bool = False
    approved_by: Optional[str] = None


_PROPOSALS: List[AdaptationProposal] = []


def submit_proposal(proposal: AdaptationProposal) -> None:
    _PROPOSALS.append(proposal)


def list_proposals(approved_only: bool = False) -> List[AdaptationProposal]:
    if approved_only:
        return [p for p in _PROPOSALS if p.approved]
    return list(_PROPOSALS)


def approve_proposal(name: str, approver: str) -> bool:
    for p in _PROPOSALS:
        if p.name == name:
            object.__setattr__(p, "approved", True)
            object.__setattr__(p, "approved_by", approver)
            return True
    return False
