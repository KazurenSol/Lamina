"""
Rule precedence logic for the legal domain.
Higher-level rules override lower-level rules deterministically.
"""
from l_cdea.domain.legal.rules import RULE_LEVEL_RANK, LegalRule


def compare_precedence(rule_a: LegalRule, rule_b: LegalRule) -> str:
    """Return 'a' if rule_a takes precedence, 'b' if rule_b does, 'equal' otherwise."""
    rank_a = RULE_LEVEL_RANK.get(rule_a.level, 999)
    rank_b = RULE_LEVEL_RANK.get(rule_b.level, 999)
    if rank_a < rank_b:
        return "a"
    if rank_b < rank_a:
        return "b"
    return "equal"


def resolve_by_specificity(rule_a: LegalRule, rule_b: LegalRule) -> str:
    """More specific rule (more conditions) wins when precedence is equal."""
    len_a = len(rule_a.conditions) + len(rule_a.prohibitions) + len(rule_a.obligations)
    len_b = len(rule_b.conditions) + len(rule_b.prohibitions) + len(rule_b.obligations)
    if len_a > len_b:
        return "a"
    if len_b > len_a:
        return "b"
    return "unresolved"


PRECEDENCE_HIERARCHY = [
    "1. Constitutional law",
    "2. Statutory law",
    "3. Regulatory rules",
    "4. Case law",
    "5. Local rules",
]
