"""
Programming equivalence rules for CAS.

x = x + 1  ==  x += 1
return f(x)  ==  result = f(x); return result  (if result unused elsewhere)
for item in col: out.append(f(item))  ==  MAP(col, f)  (no side effects)
if c: return A else: return B  ==  RETURN_VALUE(SELECT(c, A, B))
"""
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.normalization.canonicalizer.signature import compute_signature


def are_programming_equivalent(g1: CDLGraph, g2: CDLGraph) -> bool:
    return compute_signature(g1) == compute_signature(g2)


EQUIVALENCE_RULES = [
    {
        "name": "increment_assign",
        "lhs": "ASSIGN(x, ADD(x, 1))",
        "rhs": "ASSIGN(x, 1)",
        "condition": "x += 1 form",
    },
    {
        "name": "inline_return",
        "lhs": "ASSIGN(result, CALL_FUNCTION(f, x)); RETURN_VALUE(result)",
        "rhs": "RETURN_VALUE(CALL_FUNCTION(f, x))",
        "condition": "result has no other uses",
    },
    {
        "name": "loop_to_map",
        "lhs": "ITERATE(collection, APPEND(output, f(item)))",
        "rhs": "MAP(collection, f)",
        "condition": "loop body has no side effects",
    },
    {
        "name": "branch_to_select",
        "lhs": "CONDITIONAL_BRANCH(cond, RETURN_VALUE(A), RETURN_VALUE(B))",
        "rhs": "RETURN_VALUE(SELECT(cond, A, B))",
        "condition": "always",
    },
]
