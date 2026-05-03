from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError

E, P, S, C, A, R, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                         SemanticType.CONSTRAINT, SemanticType.ABSTRACTION,
                         SemanticType.RELATION, SemanticType.EVENT)


def _prog(name, inputs, output, fn):
    return CDLOperator(name=f"programming.{name}",
                       signature=TypeSignature(input_types=inputs, output_type=output),
                       transform=fn)


DEFINE_VARIABLE = _prog("DEFINE_VARIABLE", (A, E), E,
    lambda name, val: TypedValue({"name": name.value, "value": val.value}, E))

ASSIGN = _prog("ASSIGN", (E, E), S,
    lambda var, val: TypedValue({"assigned": var.value, "value": val.value}, S))

DEFINE_FUNCTION = _prog("DEFINE_FUNCTION", (A, E, P), P,
    lambda name, params, body: TypedValue({"fn": name.value, "params": params.value, "body": body.value}, P))

CALL_FUNCTION = _prog("CALL_FUNCTION", (P, E), E,
    lambda fn, args: TypedValue(f"call({fn.value}, {args.value})", E))

RETURN_VALUE = _prog("RETURN_VALUE", (E,), S,
    lambda val: TypedValue({"return": val.value}, S))

EVALUATE_EXPRESSION = _prog("EVALUATE_EXPRESSION", (P,), E,
    lambda expr: TypedValue(f"eval({expr.value})", E))

CONDITIONAL_BRANCH = _prog("CONDITIONAL_BRANCH", (C, P, P), P,
    lambda cond, t, f: TypedValue(f"if({cond.value},{t.value},{f.value})", P))

ITERATE = _prog("ITERATE", (E, P), P,
    lambda coll, op: TypedValue(f"iterate({coll.value},{op.value})", P))

INDEX = _prog("INDEX", (E, E), E,
    lambda coll, pos: TypedValue(
        coll.value[pos.value] if isinstance(coll.value, (list, dict)) else f"index({coll.value},{pos.value})", E))

APPEND = _prog("APPEND", (E, E), E,
    lambda coll, val: TypedValue(
        (coll.value + [val.value]) if isinstance(coll.value, list) else f"append({coll.value},{val.value})", E))

REMOVE = _prog("REMOVE", (E, E), E,
    lambda coll, val: TypedValue(
        [x for x in coll.value if x != val.value] if isinstance(coll.value, list) else f"remove({coll.value},{val.value})", E))

LOOKUP_KEY = _prog("LOOKUP_KEY", (E, E), E,
    lambda mapping, key: TypedValue(
        mapping.value.get(key.value, None) if isinstance(mapping.value, dict) else f"lookup({key.value})", E))

SET_KEY = _prog("SET_KEY", (E, E, E), S,
    lambda mapping, key, val: TypedValue({**mapping.value, key.value: val.value} if isinstance(mapping.value, dict) else f"set({key.value}={val.value})", S))

COMPARE_VALUES = _prog("COMPARE_VALUES", (E, E, A), C,
    lambda left, right, op: TypedValue(left.value == right.value, C))

RAISE_ERROR = _prog("RAISE_ERROR", (A, E), S,
    lambda etype, msg: TypedValue({"error": etype.value, "message": msg.value}, S))

HANDLE_ERROR = _prog("HANDLE_ERROR", (S, P), S,
    lambda error, handler: TypedValue(f"handle({error.value},{handler.value})", S))

ALL_PROGRAMMING_OPERATORS = [
    DEFINE_VARIABLE, ASSIGN, DEFINE_FUNCTION, CALL_FUNCTION, RETURN_VALUE,
    EVALUATE_EXPRESSION, CONDITIONAL_BRANCH, ITERATE, INDEX, APPEND, REMOVE,
    LOOKUP_KEY, SET_KEY, COMPARE_VALUES, RAISE_ERROR, HANDLE_ERROR,
]


def register_programming_operators():
    for op in ALL_PROGRAMMING_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators():
    """Bootstrap all domain operators through the governance layer. Idempotent."""
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
