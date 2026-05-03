"""
Biological system hierarchy for the biology domain.
Systems are nested: molecule → cell → tissue → organ → organism.
"""

BIOLOGICAL_HIERARCHY = [
    "molecule",
    "organelle",
    "cell",
    "tissue",
    "organ",
    "organ_system",
    "organism",
    "population",
    "ecosystem",
]

ORGAN_SYSTEMS = {
    "circulatory":  {"organs": ["heart", "blood vessels", "blood"], "function": "transport"},
    "nervous":      {"organs": ["brain", "spinal cord", "nerves"], "function": "signaling"},
    "digestive":    {"organs": ["stomach", "intestines", "liver"], "function": "nutrient absorption"},
    "respiratory":  {"organs": ["lungs", "trachea", "bronchi"],   "function": "gas exchange"},
    "immune":       {"organs": ["lymph nodes", "spleen", "thymus"],"function": "defense"},
    "endocrine":    {"organs": ["thyroid", "adrenal glands", "pancreas"], "function": "hormone regulation"},
}

SIGNALING_TYPES = [
    "autocrine",
    "paracrine",
    "endocrine",
    "synaptic",
]
