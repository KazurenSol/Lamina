"""
Core base operators — CORE_OPS_V1 as defined in programming domain spec 2.
27 universal operators available to all domains. Named with 'core.' prefix.
"""
from __future__ import annotations

from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator

E = SemanticType.ENTITY
P = SemanticType.PROCESS
S = SemanticType.STATE
C = SemanticType.CONSTRAINT
A = SemanticType.ABSTRACTION
EV = SemanticType.EVENT


def _op(name: str, inputs: tuple, output: SemanticType, fn) -> CDLOperator:
    return CDLOperator(
        name=f"core.{name}",
        signature=TypeSignature(input_types=inputs, output_type=output),
        transform=fn,
    )


# --- Identity / structure ---

CREATE = _op("CREATE", (A, E), E,
    lambda type_spec, value: TypedValue({"type": type_spec.value, "value": value.value}, E))

DELETE = _op("DELETE", (E,), S,
    lambda entity: TypedValue({"deleted": entity.value}, S))

DEFINE = _op("DEFINE", (A,), E,
    lambda name: TypedValue(name.value, E))

CLASSIFY = _op("CLASSIFY", (E, A), E,
    lambda entity, category: TypedValue({"entity": entity.value, "class": category.value}, E))

VALIDATE = _op("VALIDATE", (E, C), C,
    lambda entity, constraint: TypedValue(
        {"valid": True, "entity": entity.value}
        if constraint.value is True
        else {"valid": False, "entity": entity.value, "constraint": constraint.value}, C))

# --- Collection operations ---

CONTAIN = _op("CONTAIN", (E, E), C,
    lambda collection, element: TypedValue(
        element.value in collection.value
        if isinstance(collection.value, (list, set, tuple))
        else f"({element.value}∈{collection.value})", C))

LOOKUP = _op("LOOKUP", (E, E), E,
    lambda key, mapping: TypedValue(
        mapping.value.get(key.value)
        if isinstance(mapping.value, dict)
        else f"lookup({key.value})", E))

SELECT = _op("SELECT", (C, E, E), E,
    lambda cond, t, f: t if (cond.value is True or cond.value == "true") else f)

FILTER = _op("FILTER", (E, C), E,
    lambda collection, pred: TypedValue(f"filter({collection.value}, {pred.value})", E))

MAP = _op("MAP", (E, P), E,
    lambda collection, op: TypedValue(f"map({op.value}, {collection.value})", E))

REDUCE = _op("REDUCE", (E, P, E), E,
    lambda collection, op, initial: TypedValue(
        f"reduce({op.value}, {collection.value}, init={initial.value})", E))

SORT = _op("SORT", (E, C), E,
    lambda collection, criterion: TypedValue(
        sorted(collection.value, key=lambda x: x)
        if isinstance(collection.value, list)
        else f"sort({collection.value}, {criterion.value})", E))

GROUP = _op("GROUP", (E, A), E,
    lambda collection, attr: TypedValue(f"group({collection.value}, by={attr.value})", E))

COUNT = _op("COUNT", (E,), E,
    lambda collection: TypedValue(
        len(collection.value)
        if isinstance(collection.value, (list, set, tuple, dict))
        else f"count({collection.value})", E))

# --- Relation operations ---

CONNECT = _op("CONNECT", (E, E), S,
    lambda a, b: TypedValue({"connected": [a.value, b.value]}, S))

DISCONNECT = _op("DISCONNECT", (E, E), S,
    lambda a, b: TypedValue({"disconnected": [a.value, b.value]}, S))

COMPARE = _op("COMPARE", (E, E), C,
    lambda a, b: TypedValue(a.value == b.value, C))

MATCH = _op("MATCH", (E, C), C,
    lambda entity, pattern: TypedValue(f"match({entity.value}, {pattern.value})", C))

# --- Transformation ---

TRANSFORM = _op("TRANSFORM", (E, A), S,
    lambda entity, rule: TypedValue(f"transform({entity.value}, {rule.value})", S))

MERGE = _op("MERGE", (E, E), E,
    lambda a, b: TypedValue(
        {**a.value, **b.value}
        if isinstance(a.value, dict) and isinstance(b.value, dict)
        else f"merge({a.value}, {b.value})", E))

SPLIT = _op("SPLIT", (E, C), E,
    lambda entity, criterion: TypedValue(f"split({entity.value}, {criterion.value})", E))

CONVERT = _op("CONVERT", (E, A), E,
    lambda entity, target_type: TypedValue({"value": entity.value, "as": target_type.value}, E))

# --- Control / execution ---

EXECUTE = _op("EXECUTE", (P, E), E,
    lambda proc, arg: TypedValue(f"execute({proc.value}, {arg.value})", E))

QUERY = _op("QUERY", (E, C), E,
    lambda source, constraint: TypedValue(f"query({source.value}, {constraint.value})", E))

RETURN = _op("RETURN", (E,), E,
    lambda val: TypedValue(val.value, E))

# --- Observation / measurement ---

OBSERVE = _op("OBSERVE", (E,), EV,
    lambda entity: TypedValue({"observed": entity.value}, EV))

MEASURE = _op("MEASURE", (E,), E,
    lambda qty: TypedValue(
        qty.value.get("value", qty.value)
        if isinstance(qty.value, dict)
        else qty.value, E))

# Kept for backward compatibility with domain specs that reference them by these names
DEFINE_ENTITY = _op("DEFINE_ENTITY", (A,), E,
    lambda name: TypedValue(name.value, E))

DEFINE_PROCESS = _op("DEFINE_PROCESS", (A,), P,
    lambda name: TypedValue(name.value, P))

ALL_BASE_OPERATORS = [
    CREATE, DELETE, DEFINE, CLASSIFY, VALIDATE,
    CONTAIN, LOOKUP, SELECT, FILTER, MAP, REDUCE, SORT, GROUP, COUNT,
    CONNECT, DISCONNECT, COMPARE, MATCH,
    TRANSFORM, MERGE, SPLIT, CONVERT,
    EXECUTE, QUERY, RETURN,
    OBSERVE, MEASURE,
    DEFINE_ENTITY, DEFINE_PROCESS,
]
