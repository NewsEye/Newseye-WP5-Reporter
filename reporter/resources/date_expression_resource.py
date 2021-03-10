from typing import Dict, List, Union

Val = Union[str, List[str]]

ENGLISH: Dict[str, Union[Val, Dict[str, Val]]] = {
    "month": {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December",
        "reference_options": "the same month",
    },
    "year": {"reference_options": "the same year"},
    "month-expression": "{month}",
    "month-year-expression": "{month} {year}",
    "year-expression": "{year}",
    "between-expression": "between {start} and {end}",
}

GERMAN: Dict[str, Union[Val, Dict[str, Val]]] = {
    "month": {
        "01": "Januar",
        "02": "Februar",
        "03": "März",
        "04": "April",
        "05": "Mai",
        "06": "Juni",
        "07": "Juli",
        "08": "August",
        "09": "September",
        "10": "Oktober",
        "11": "November",
        "12": "Dezember",
        "reference_options": ["auch im selben Monat", "gleichzeitich"],
    },
    "year": {"reference_options": ["auch im selben Jahr", "gleichzeitich"]},
    "month-expression": "{month}",
    "month-year-expression": "{month} {year}",
    "year-expression": "{year}",
    "between-expression": "zwischen {start} und {end}",
}

FRENCH: Dict[str, Union[Val, Dict[str, Val]]] = {
    "month": {
        "01": "janvier",
        "02": "février",
        "03": "mars",
        "04": "avril",
        "05": "mai",
        "06": "juin",
        "07": "juillet",
        "08": "août",
        "09": "septembre",
        "10": "octobre",
        "11": "november",
        "12": "décembre",
        "reference_options": ["le même mois"],
    },
    "year": {"reference_options": ["la même année"]},
    "month-expression": "{month}",
    "month-year-expression": "en {month} {year}",
    "year-expression": "{year}",
    "between-expression": "entre {start} et {end}",
}

FINNISH: Dict[str, Union[Val, Dict[str, Val]]] = {
    "month": {
        "01": "tammikuu",
        "02": "helmikuu",
        "03": "maaliskuu",
        "04": "huhtikuu",
        "05": "toukokuu",
        "06": "kesäkuu",
        "07": "heinäkuu",
        "08": "elokuu",
        "09": "syyskuu",
        "10": "lokakuu",
        "11": "marraskuu",
        "12": "joulukuu",
        "reference_options": ["kyseisessä kuussa", "samaan aikaan"],
    },
    "year": {"reference_options": ["samana vuonna", "myös samana vuonna"]},
    "month-expression": "{month}",
    "month-year-expression": "{month} {year}",
    "year-expression": "{year}",
    "between-expression": "{start} ja {end} välillä",
}
