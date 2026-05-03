from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError

E, P, S, C, A = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                  SemanticType.CONSTRAINT, SemanticType.ABSTRACTION)


def _math(name, inputs, output, fn):
    return CDLOperator(name=f"math.{name}",
                       signature=TypeSignature(input_types=inputs, output_type=output),
                       transform=fn)


def _num(a, b, op):
    if isinstance(a.value, (int, float)) and isinstance(b.value, (int, float)):
        return TypedValue(op(a.value, b.value), E)
    return TypedValue(f"({a.value} {op.__name__} {b.value})", E)


ADD      = _math("ADD",      (E, E), E, lambda a, b: TypedValue(a.value + b.value if all(isinstance(x.value, (int, float)) for x in [a,b]) else f"({a.value}+{b.value})", E))
SUBTRACT = _math("SUBTRACT", (E, E), E, lambda a, b: TypedValue(a.value - b.value if all(isinstance(x.value, (int, float)) for x in [a,b]) else f"({a.value}-{b.value})", E))
MULTIPLY = _math("MULTIPLY", (E, E), E, lambda a, b: TypedValue(a.value * b.value if all(isinstance(x.value, (int, float)) for x in [a,b]) else f"({a.value}*{b.value})", E))
DIVIDE   = _math("DIVIDE",   (E, E), E, lambda a, b: TypedValue(a.value / b.value if all(isinstance(x.value, (int, float)) for x in [a,b]) and b.value != 0 else f"({a.value}/{b.value})", E))
POWER    = _math("POWER",    (E, E), E, lambda base, exp: TypedValue(base.value ** exp.value if all(isinstance(x.value, (int, float)) for x in [base,exp]) else f"({base.value}^{exp.value})", E))

def _realize_simplify(expr):
    from l_cdea.domain.math.realization import realize_simplify
    trace = realize_simplify(str(expr.value))
    return TypedValue(trace.output_expression, P)

def _realize_expand(expr):
    from l_cdea.domain.math.realization import realize_expand
    trace = realize_expand(str(expr.value))
    return TypedValue(trace.output_expression, P)

SIMPLIFY = _math("SIMPLIFY", (P,), P, _realize_simplify)

EXPAND   = _math("EXPAND",   (P,), P, _realize_expand)

FACTOR   = _math("FACTOR",   (P,), P,
    lambda expr: TypedValue(f"factor({expr.value})", P))

SUBSTITUTE = _math("SUBSTITUTE", (P, E, E), P,
    lambda expr, var, val: TypedValue(str(expr.value).replace(str(var.value), str(val.value)), P))

SOLVE    = _math("SOLVE",    (C, E), E,
    lambda eq, var: TypedValue(f"solve({eq.value}, {var.value})", E))

IS_EQUAL = _math("IS_EQUAL", (E, E), C,
    lambda a, b: TypedValue(a.value == b.value, C))

COMPARE  = _math("COMPARE",  (E, E), C,
    lambda a, b: TypedValue({"lt": a.value < b.value, "eq": a.value == b.value, "gt": a.value > b.value} if all(isinstance(x.value, (int, float)) for x in [a,b]) else f"compare({a.value},{b.value})", C))

DEFINE_FUNCTION = _math("DEFINE_FUNCTION", (A, E, P), P,
    lambda name, params, expr: TypedValue({"fn": name.value, "params": params.value, "expr": expr.value}, P))

EVALUATE_FUNCTION = _math("EVALUATE_FUNCTION", (P, E), E,
    lambda fn, x: TypedValue(f"eval_fn({fn.value},{x.value})", E))

DERIVE    = _math("DERIVE",    (P, E), P,
    lambda expr, var: TypedValue(f"d/d{var.value}({expr.value})", P))

INTEGRATE = _math("INTEGRATE", (P, E), P,
    lambda expr, var: TypedValue(f"∫({expr.value})d{var.value}", P))

UNION        = _math("UNION",        (E, E), E, lambda a, b: TypedValue(f"({a.value}∪{b.value})", E))
INTERSECTION = _math("INTERSECTION", (E, E), E, lambda a, b: TypedValue(f"({a.value}∩{b.value})", E))
CONTAINS     = _math("CONTAINS",     (E, E), C, lambda s, e: TypedValue(e.value in s.value if isinstance(s.value, (list, set)) else f"({e.value}∈{s.value})", C))

ALL_MATH_OPERATORS = [
    ADD, SUBTRACT, MULTIPLY, DIVIDE, POWER, SIMPLIFY, EXPAND, FACTOR, SUBSTITUTE,
    SOLVE, IS_EQUAL, COMPARE, DEFINE_FUNCTION, EVALUATE_FUNCTION, DERIVE, INTEGRATE,
    UNION, INTERSECTION, CONTAINS,
]


def register_math_operators():
    for op in ALL_MATH_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators():
    """Bootstrap all domain operators through the governance layer. Idempotent."""
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
