def test_biology_operators():
    import l_cdea.domain.biology
    from l_cdea.core.cdl.registry import OperatorRegistry
    from l_cdea.core.types.base import SemanticType, TypedValue
    from l_cdea.domain.biology.operators import (
        PHOTOSYNTHESIS, CELL_RESPIRATION, PROTEIN_SYNTHESIS,
        ACTIVATE, INHIBIT, SEND_SIGNAL,
    )

    assert "biology.PHOTOSYNTHESIS" in OperatorRegistry.list()
    assert "biology.CELL_RESPIRATION" in OperatorRegistry.list()
    assert "biology.PROTEIN_SYNTHESIS" in OperatorRegistry.list()

    E, P, S, EV = (SemanticType.ENTITY, SemanticType.PROCESS,
                   SemanticType.STATE, SemanticType.EVENT)

    inputs = TypedValue({"CO2": 6, "H2O": 6, "light": 1}, E)
    result = PHOTOSYNTHESIS.execute(inputs)
    assert result.type == E
    assert result.value["process"] == "photosynthesis"

    dna = TypedValue("ATCG", E)
    protein = PROTEIN_SYNTHESIS.execute(dna)
    assert "DNA→RNA" in str(protein.value)

    proc = TypedValue("cell_respiration", P)
    activated = ACTIVATE.execute(proc)
    assert activated.value["activated"] == "cell_respiration"

    inhibited = INHIBIT.execute(proc)
    assert inhibited.value["inhibited"] == "cell_respiration"

    print("Biology tests PASSED")


if __name__ == "__main__":
    test_biology_operators()
