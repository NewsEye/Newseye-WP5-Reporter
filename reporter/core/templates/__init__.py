def canonical_map(map_dict):
    return dict(
        (alt_val, canonical) for (canonical, alt_vals) in map_dict.items() for alt_val in ([canonical] + alt_vals)
    )


# Defines alternative, equivalent field names for use in templates
# The alternatives get mapped to their canonical form (key) early in processing
FACT_FIELD_ALIASES = {
    "what_type": ["value_type", "unit"],
    "what": ["value"],
    "where_type": ["place_type"],
    "where": ["place"],
    "when_1": [],
    "when_2": [],
    "time": [],
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
