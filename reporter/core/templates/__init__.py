def canonical_map(map_dict):
    return dict(
        (alt_val, canonical) for (canonical, alt_vals) in map_dict.items() for alt_val in ([canonical] + alt_vals)
    )


# Defines alternative, equivalent field names for use in templates
# The alternatives get mapped to their canonical form (key) early in processing
# TODO: Autogenerate from Fact and/or extract from core.
FACT_FIELD_ALIASES = {
    'corpus': [],
    'corpus_type': [],
    'timestamp_from': ['timestamp', 'time'],
    'timestamp_to': [],
    'timestamp_type': [],
    'analysis_type': [],
    'result_key': [],
    'result_value': [],
}
FACT_FIELD_MAP = canonical_map(FACT_FIELD_ALIASES)

# Similarly, we have multiple ways to refer to location types
LOCATION_TYPES = {
    "C": ["country"],
    "D": ["district"],
    "M": ["municipality", "mun"],
}
LOCATION_TYPE_MAP = canonical_map(LOCATION_TYPES)


FACT_FIELDS = FACT_FIELD_ALIASES.keys()
