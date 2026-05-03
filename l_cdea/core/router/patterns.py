from __future__ import annotations

from typing import Callable, Dict, List, Optional

from l_cdea.core.router.intent import PatternRule


class PatternRegistry:
    """
    Central store of all domain PatternRules.
    Domains call register_patterns(registry) to add their rules.
    Deterministic: iteration order is insertion order, tie-breaking is explicit.
    """

    def __init__(self) -> None:
        self._rules: Dict[str, PatternRule] = {}  # keyed by rule.id

    def register(self, rule: PatternRule) -> None:
        if rule.id in self._rules:
            return  # idempotent
        self._rules[rule.id] = rule

    def all_rules(self) -> List[PatternRule]:
        return list(self._rules.values())

    def rules_for_domain(self, domain: str) -> List[PatternRule]:
        return [r for r in self._rules.values() if r.domain == domain]

    def get(self, rule_id: str) -> Optional[PatternRule]:
        return self._rules.get(rule_id)

    def __len__(self) -> int:
        return len(self._rules)


# Module-level singleton
_REGISTRY = PatternRegistry()


def get_registry() -> PatternRegistry:
    return _REGISTRY


def register_rule(rule: PatternRule) -> None:
    _REGISTRY.register(rule)


# ---------------------------------------------------------------------------
# Domain pattern loader
# ---------------------------------------------------------------------------

def load_domain_patterns() -> None:
    """
    Import each domain's compiler_bindings and call register_patterns(registry)
    if the function exists. Safe to call multiple times — registry is idempotent.
    """
    domains = [
        "l_cdea.discourse.definition_retrieval.patterns",   # discourse definitions first (highest priority)
        "l_cdea.core.router.paraphrase_patterns",            # paraphrase expansions (priority 190–202)
        "l_cdea.discourse.composition_reasoning.patterns",  # composition queries (priority 196)
        "l_cdea.discourse.multi_hop_reasoning.patterns",    # multi-hop queries (priority 195)
        "l_cdea.discourse.relationship_query.patterns",     # one-hop relationship queries (priority 190)
        "l_cdea.domain.geography.compiler_bindings",
        "l_cdea.domain.programming.compiler_bindings",
        "l_cdea.domain.math.compiler_bindings",
        "l_cdea.domain.physics.compiler_bindings",
        "l_cdea.domain.biology.compiler_bindings",
        "l_cdea.domain.finance.compiler_bindings",
        "l_cdea.domain.legal.compiler_bindings",
    ]
    import importlib
    for mod_path in domains:
        try:
            mod = importlib.import_module(mod_path)
            if hasattr(mod, "register_patterns"):
                mod.register_patterns(_REGISTRY)
        except ImportError:
            pass
