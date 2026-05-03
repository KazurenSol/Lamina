"""
PatternRule definitions for the ingestion router.

Each PatternRule is matched against a normalized (lowercase-stripped) chunk.

Matching:
  keywords — each must appear as a whole phrase (word-boundary aware)
  structure — compiled regex applied to the text; match counts as 1 hit

Scoring:
  score = keyword_hit_count + (1 if structure matches) + priority
  Scores for all rules in the same category are SUMMED.

Priority order (higher wins ties):
  formula    5  — highest: structural math overrides semantic categories
  definition 3
  example    3
  procedure  4
  claim      2  — most common pattern; lowest priority prevents false positives
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True)
class PatternRule:
    id: str
    category: str
    keywords: Tuple[str, ...]
    structure: Optional[str]   # regex string; None = no structural check
    priority: int

    def compiled_structure(self):
        if self.structure is None:
            return None
        return re.compile(self.structure, re.IGNORECASE)


# ── Formula patterns (priority 5) ─────────────────────────────────────────────
# Detected purely by structure — no keywords needed.
# A chunk qualifies as formula if it contains "=" (equality) or
# multiple math operators in proximity to variable-like tokens.

FORMULA_RULES: Tuple[PatternRule, ...] = (
    PatternRule(
        id="formula.equals",
        category="formula",
        keywords=(),
        structure=r"[\w\d]\s*=\s*[\w\d]",   # word = word (e.g. "F = ma")
        priority=5,
    ),
    PatternRule(
        id="formula.math_ops",
        category="formula",
        keywords=(),
        # Two or more math operators in close proximity with variable-like tokens
        structure=r"[\w\d][\s\w\d]*[\+\-\*\/\^][\s\w\d]*[\+\-\*\/\^][\s\w\d]*[\w\d]",
        priority=5,
    ),
    PatternRule(
        id="formula.single_op_with_var",
        category="formula",
        keywords=(),
        # Single operator flanked by alphanumeric tokens, like "x^2" or "2*x"
        structure=r"[a-zA-Z]\w*\s*[\^]\s*\d|[a-zA-Z]\w*\s*[\*\/]\s*[a-zA-Z]",
        priority=4,
    ),
)

# ── Definition patterns (priority 3) ──────────────────────────────────────────

DEFINITION_RULES: Tuple[PatternRule, ...] = (
    PatternRule(
        id="definition.is_defined_as",
        category="definition",
        keywords=("is defined as", "is known as", "is described as"),
        structure=None,
        priority=3,
    ),
    PatternRule(
        id="definition.refers_to",
        category="definition",
        keywords=("refers to", "denotes", "designates"),
        structure=None,
        priority=3,
    ),
    PatternRule(
        id="definition.means",
        category="definition",
        keywords=("means", "is called", "is termed"),
        structure=None,
        priority=3,
    ),
    PatternRule(
        id="definition.is_a",
        category="definition",
        keywords=("is a type of", "is an instance of", "is a kind of"),
        structure=None,
        priority=3,
    ),
    PatternRule(
        id="definition.structural",
        category="definition",
        keywords=(),
        # "Term: definition" or "Term — definition" structural cue
        structure=r"^[A-Za-z][^:]{1,40}:\s+\S",
        priority=2,
    ),
)

# ── Procedure patterns (priority 4) ───────────────────────────────────────────

PROCEDURE_RULES: Tuple[PatternRule, ...] = (
    PatternRule(
        id="procedure.ordinal_keywords",
        category="procedure",
        keywords=("first", "second", "third", "then", "next", "finally",
                  "after that", "subsequently"),
        structure=None,
        priority=4,
    ),
    PatternRule(
        id="procedure.step_keyword",
        category="procedure",
        keywords=("step", "steps", "begin by", "start by", "proceed to"),
        structure=None,
        priority=4,
    ),
    PatternRule(
        id="procedure.action_sequence",
        category="procedure",
        keywords=(),
        # "First, ...", "Step 1:", "Then ..." structural cues
        structure=r"^(step\s+\d|first\b|then\b|next\b|finally\b)",
        priority=4,
    ),
)

# ── Example patterns (priority 3) ─────────────────────────────────────────────

EXAMPLE_RULES: Tuple[PatternRule, ...] = (
    PatternRule(
        id="example.for_example",
        category="example",
        keywords=("for example", "for instance", "as an example"),
        structure=None,
        priority=3,
    ),
    PatternRule(
        id="example.abbreviations",
        category="example",
        keywords=("e.g.", "i.e.", "such as", "including", "like"),
        structure=None,
        priority=3,
    ),
    PatternRule(
        id="example.consider",
        category="example",
        keywords=("consider", "take the case", "suppose that",
                  "imagine", "assume"),
        structure=None,
        priority=2,
    ),
)

# ── Claim patterns (priority 2, lowest) ───────────────────────────────────────

CLAIM_RULES: Tuple[PatternRule, ...] = (
    PatternRule(
        id="claim.relational",
        category="claim",
        keywords=("causes", "results in", "leads to", "produces",
                  "prevents", "enables", "increases", "decreases"),
        structure=None,
        priority=2,
    ),
    PatternRule(
        id="claim.state",
        category="claim",
        keywords=("is", "are", "has", "have", "was", "were", "equals",
                  "contains", "consists of"),
        structure=None,
        priority=2,
    ),
    PatternRule(
        id="claim.factual",
        category="claim",
        keywords=("always", "never", "must", "cannot", "all", "every",
                  "none", "typically"),
        structure=None,
        priority=2,
    ),
)


# ── Master list ────────────────────────────────────────────────────────────────

ALL_RULES: Tuple[PatternRule, ...] = (
    *FORMULA_RULES,
    *DEFINITION_RULES,
    *PROCEDURE_RULES,
    *EXAMPLE_RULES,
    *CLAIM_RULES,
)
