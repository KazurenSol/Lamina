"""
Known biological process chains for the biology domain.
All processes are represented as deterministic input→output mappings.
"""

BIOLOGICAL_PROCESSES = {
    "photosynthesis": {
        "inputs":  ["light", "CO2", "water"],
        "outputs": ["glucose", "oxygen"],
        "steps":   ["light absorption", "Calvin cycle", "glucose synthesis"],
    },
    "cell_respiration": {
        "inputs":  ["glucose", "oxygen"],
        "outputs": ["ATP", "CO2", "water"],
        "steps":   ["glycolysis", "Krebs cycle", "electron transport chain"],
    },
    "protein_synthesis": {
        "inputs":  ["DNA"],
        "outputs": ["protein"],
        "steps":   ["transcription (DNA→RNA)", "translation (RNA→protein)"],
    },
    "cell_division_mitosis": {
        "inputs":  ["cell"],
        "outputs": ["2 daughter cells (identical)"],
        "steps":   ["prophase", "metaphase", "anaphase", "telophase", "cytokinesis"],
    },
    "cell_division_meiosis": {
        "inputs":  ["germ cell"],
        "outputs": ["4 haploid gametes"],
        "steps":   ["meiosis I", "meiosis II"],
    },
}

PROCESS_CHAIN_RULES = [
    {"name": "central_dogma", "chain": "DNA → RNA → Protein"},
    {"name": "energy_flow",   "chain": "light → chemical energy → ATP"},
]
