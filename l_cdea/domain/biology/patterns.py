"""Reusable biology discourse patterns."""
BIOLOGY_PATTERNS = [
    {"name": "photosynthesis",     "frame": "PHOTOSYNTHESIS",    "slots": ("inputs",)},
    {"name": "cell_respiration",   "frame": "CELL_RESPIRATION",  "slots": ("inputs",)},
    {"name": "protein_production", "frame": "PROTEIN_SYNTHESIS", "slots": ("dna",)},
    {"name": "substance_convert",  "frame": "CONVERT_SUBSTANCE", "slots": ("input", "output")},
    {"name": "cell_division",      "frame": "DIVIDE_CELL",       "slots": ("cell",)},
    {"name": "signal_pathway",     "frame": "SEND_SIGNAL",       "slots": ("source", "target", "signal")},
    {"name": "process_activate",   "frame": "ACTIVATE",          "slots": ("process",)},
    {"name": "process_inhibit",    "frame": "INHIBIT",           "slots": ("process",)},
]
