from reporter.resources.processor_resource import ProcessorResource

TEMPLATE = """
en: there were {result_value} entries {result_key}
fi: löydettiin {result_value} {result_key} tulosta
de: es gibt {result_value} Einträge zu {result_key}
| analysis_type = facet_count

en: there were {result_value} entries {result_key}
fi: kielellä {result_key} löytyi {result_value} osumaa
de: es gibt {result_value} Einträge {result_key}
| analysis_type = facet_count_language_ssi

en: there were {result_value} entries {result_key}
fi: löydettiin {result_value} osumaa jotka oli julkaistu {result_key}
de: es gibt {result_value} Einträge veröffentlicht {result_key}
| analysis_type = facet_count_date_created_dtsi

en: there were {result_value} entries published {result_key}
fi: löydettiin {result_value} osumaa jotka oli julkaistu vuonna {result_key}
de: es gibt {result_value} Einträge veröffentlicht {result_key}
| analysis_type = facet_count_year_isi

en: there were {result_value} hits in {result_key}
fi: löytyi {result_value} tulosta, jotka oli julkaistu lehdessä {result_key}
de: es gibt {result_value} Ergebnisse in {result_key}
| analysis_type = facet_count_member_of_collection_ids_ssim

en: there were {result_value} entries in {result_key}
fi: löydettiin {result_value} osumaa jotka olivat {result_key} -tyyppisissä dokumenteissa
de: es gibt {result_value} Einträge {result_key}
| analysis_type = facet_count_has_model_ssim
"""


class FacetCountResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE
