"""
Contradiction detection for the legal domain.
Contradictions are flagged deterministically; resolution defers to precedence.
"""
from l_cdea.domain.legal.rules import LegalRule
from l_cdea.domain.legal.precedence import compare_precedence, resolve_by_specificity


def rules_contradict(rule_a: LegalRule, rule_b: LegalRule) -> bool:
    """Two rules contradict if one prohibits what the other obliges."""
    for prohibition in rule_a.prohibitions:
        if prohibition in rule_b.obligations:
            return True
    for prohibition in rule_b.prohibitions:
        if prohibition in rule_a.obligations:
            return True
    return False


def resolve_contradiction(rule_a: LegalRule, rule_b: LegalRule) -> dict:
    """Attempt to resolve a contradiction between two rules. Returns resolution dict."""
    precedence = compare_precedence(rule_a, rule_b)
    if precedence == "a":
        return {"winner": rule_a.name, "method": "precedence", "loser": rule_b.name}
    if precedence == "b":
        return {"winner": rule_b.name, "method": "precedence", "loser": rule_a.name}
    specificity = resolve_by_specificity(rule_a, rule_b)
    if specificity == "a":
        return {"winner": rule_a.name, "method": "specificity", "loser": rule_b.name}
    if specificity == "b":
        return {"winner": rule_b.name, "method": "specificity", "loser": rule_a.name}
    return {"winner": None, "method": "unresolved",
            "conflict_between": [rule_a.name, rule_b.name]}
