import datetime
import gzip
import itertools
import json
import logging
import os
import pickle
import random
from collections import defaultdict
from typing import Callable, Dict, Iterable, List, Optional, Tuple, TypeVar, Union

from reporter.constants import CONJUNCTIONS, get_error_message
from reporter.core.aggregator import Aggregator
from reporter.core.document_planner import NoInterestingMessagesException
from reporter.core.models import Template
from reporter.core.morphological_realizer import MorphologicalRealizer
from reporter.core.pipeline import NLGPipeline, NLGPipelineComponent
from reporter.core.realize_slots import SlotRealizer
from reporter.core.registry import Registry
from reporter.core.surface_realizer import (
    BodyHTMLListSurfaceRealizer,
    BodyHTMLOrderedListSurfaceRealizer,
    BodyHTMLSurfaceRealizer,
    HeadlineHTMLSurfaceRealizer,
)
from reporter.core.template_reader import read_templates
from reporter.core.template_selector import TemplateSelector
from reporter.english_uralicNLP_morphological_realizer import EnglishUralicNLPMorphologicalRealizer
from reporter.finnish_uralicNLP_morphological_realizer import FinnishUralicNLPMorphologicalRealizer
from reporter.link_remover import LinkRemover
from reporter.newspaper_document_planner import (
    NewspaperBodyDocumentPlanner,
    NewspaperHeadlineDocumentPlanner,
    MAX_PARAGRAPHS,
)
from reporter.newspaper_importance_allocator import NewspaperImportanceSelector
from reporter.newspaper_message_generator import NewspaperMessageGenerator, NoMessagesForSelectionException
from reporter.newspaper_named_entity_resolver import NewspaperEntityNameResolver
from reporter.resources.extract_bigrams_resource import ExtractBigramsResource
from reporter.resources.extract_facets_resource import ExtractFacetsResource
from reporter.resources.extract_names_resource import ExtractNamesResource
from reporter.resources.extract_words_resource import ExtractWordsResource
from reporter.resources.generate_time_series_resource import GenerateTimeSeriesResource
from reporter.resources.newspaper_corpus_resource import NewspaperCorpusResource
from reporter.resources.processor_resource import ProcessorResource
from reporter.resources.query_topic_model_resource import QueryTopicModelResource
from reporter.resources.summarization_resource import SummarizationResource
from reporter.resources.topic_model_docset_comparison_resource import TopicModelDocsetComparisonResource
from reporter.resources.topic_model_document_linking_resource import TopicModelDocumentLinkingResource
from reporter.resources.track_name_sentiment_resource import TrackNameSentimentResource

log = logging.getLogger("root")


class NewspaperNlgService(object):

    processor_resources: List[ProcessorResource] = []

    # These are (re)initialized every time run_pipeline is called
    body_pipeline = None
    headline_pipeline = None

    def __init__(self, random_seed: int = None) -> None:
        """
        :param random_seed: seed for random number generation, for repeatability
        """

        # New registry and result importer
        self.registry = Registry()

        # Per-processor resources
        self.processor_resources = [
            NewspaperCorpusResource(),
            ExtractWordsResource(),
            ExtractBigramsResource(),
            ExtractFacetsResource(),
            GenerateTimeSeriesResource(),
            SummarizationResource(),
            TopicModelDocumentLinkingResource(),
            QueryTopicModelResource(),
            TopicModelDocsetComparisonResource(),
            ExtractNamesResource(),
            TrackNameSentimentResource(),
        ]

        # Templates
        self.registry.register(
            "templates",
            self._get_cached_or_compute("../data/templates.cache", self._load_templates, force_cache_refresh=True),
        )

        # Misc language data
        self.registry.register("CONJUNCTIONS", CONJUNCTIONS)

        # PRNG seed
        self._set_seed(seed_val=random_seed)

        # Message Parsers
        self.registry.register("message-parsers", [])
        for processor_resource in self.processor_resources:
            self.registry.get("message-parsers").append(processor_resource.parse_messages)

        # Slot Realizers Components
        self.registry.register("slot-realizers", [])
        for processor_resource in self.processor_resources:
            components = [component(self.registry) for component in processor_resource.slot_realizer_components()]
            self.registry.get("slot-realizers").extend(components)

    T = TypeVar("T")

    def _get_cached_or_compute(
        self, cache: str, compute: Callable[..., T], force_cache_refresh: bool = False, relative_path: bool = True
    ) -> T:  # noqa: F821 -- Needed until https://github.com/PyCQA/pyflakes/issues/427 reaches a release
        if relative_path:
            cache = os.path.abspath(os.path.join(os.path.dirname(__file__), cache))
        if force_cache_refresh:
            log.info("force_cache_refresh is True, deleting previous cache from {}".format(cache))
            if os.path.exists(cache):
                os.remove(cache)
        if not os.path.exists(cache):
            log.info("No cache at {}, computing".format(cache))
            result = compute()
            if not os.path.exists(os.path.dirname(cache)):
                os.makedirs(os.path.dirname(cache))
            with gzip.open(cache, "wb") as f:
                pickle.dump(result, f)
            return result
        else:
            log.info("Found cache at {}, decompressing and loading".format(cache))
            with gzip.open(cache, "rb") as f:
                return pickle.load(f)

    def _load_templates(self) -> Dict[str, List[Template]]:
        log.info("Loading templates")
        templates: Dict[str, List[Template]] = defaultdict(list)
        for resource in self.processor_resources:
            for language, new_templates in read_templates(resource.templates_string())[0].items():
                templates[language].extend(new_templates)
        return templates

    def _get_components(self, realizer: str, links: bool) -> Iterable[NLGPipelineComponent]:
        yield NewspaperMessageGenerator()
        yield NewspaperImportanceSelector()

        if realizer == "headline":
            yield NewspaperHeadlineDocumentPlanner()
        else:
            yield NewspaperBodyDocumentPlanner()

        yield TemplateSelector()
        yield Aggregator()
        yield SlotRealizer()
        yield NewspaperEntityNameResolver()

        yield MorphologicalRealizer(
            {"fi": FinnishUralicNLPMorphologicalRealizer(), "en": EnglishUralicNLPMorphologicalRealizer()}
        )

        if realizer == "headline":
            yield HeadlineHTMLSurfaceRealizer()
        elif realizer == "ol":
            yield BodyHTMLOrderedListSurfaceRealizer()
        elif realizer == "ul":
            yield BodyHTMLListSurfaceRealizer()
        else:
            yield BodyHTMLSurfaceRealizer()

        if not links:
            yield LinkRemover()

    def run_pipeline(
        self, language: str, output_format: str, data: str, links: bool
    ) -> Tuple[Union[str, List[str]], Union[str, List[str]], List[str]]:
        start_time = datetime.datetime.now().timestamp()
        log.info("Starting multi-part generation")
        data = json.loads(data)
        splits: Dict[str, List[str]] = defaultdict(list)
        for result in data:
            key = json.dumps(
                {
                    "dataset": result.get("dataset"),
                    "query": result.get("search_query"),
                    "processor": result.get("processor"),
                }
            )
            splits[key].append(result)

        outputs: List[Tuple[str, str, float, List[str]]] = []
        for split in splits.values():
            json_split = json.dumps(split)
            outputs.append(self.run_pipeline_single(language, output_format, json_split, links))

        # Limit outputs to top MAX_PARAGRAPHS outputs
        outputs = sorted(outputs, key=lambda x: x[2])[:MAX_PARAGRAPHS]

        # Group outputs by header
        outputs = sorted(outputs, key=lambda output: output[0])
        outputs = [list(group) for _, group in itertools.groupby(outputs, key=lambda x: x[0])]

        # Sort each group by score
        outputs = [sorted(group, key=lambda output: output[2], reverse=True) for group in outputs]

        # Calc max score for each group
        outputs = [(group, max(output[2] for output in group)) for group in outputs]

        # Sort group by max score
        outputs = sorted(outputs, key=lambda x: x[1], reverse=True)

        # Remove max scores
        outputs = [grp for (grp, score) in outputs]

        # Flatten groups to single list
        outputs = list(itertools.chain.from_iterable(outputs))

        bodies, headlines, _, errors = zip(*outputs)
        errors = list(itertools.chain.from_iterable(errors))

        end_time = datetime.datetime.now().timestamp()
        log.info("Multi-part generation complete. Generation time in seconds: {}".format(end_time - start_time))

        return bodies, headlines, errors

    def run_pipeline_single(
        self, language: str, output_format: str, data: str, links: bool
    ) -> Tuple[str, str, float, List[str]]:
        log.info("Configuring Body NLG Pipeline")
        self.body_pipeline = NLGPipeline(self.registry, *self._get_components(output_format, links))
        self.headline_pipeline = NLGPipeline(self.registry, *self._get_components("headline", links))

        errors: List[str] = []

        log.info("Running Body NLG pipeline: language={}".format(language))
        try:
            body, max_score = self.body_pipeline.run((data,), language, prng_seed=self.registry.get("seed"))
            log.info("Body pipeline complete")
        except NoMessagesForSelectionException as ex:
            log.error("%s", ex)
            body, max_score = get_error_message(language, "no-messages-for-selection"), 0
            errors.append("NoMessagesForSelectionException")
        except NoInterestingMessagesException as ex:
            log.info("%s", ex)
            body, max_score = get_error_message(language, "no-interesting-messages-for-selection"), 0
            errors.append("NoInterestingMessagesException")
        except Exception as ex:
            log.exception("%s", ex)
            body, max_score = get_error_message(language, "general-error"), 0
            errors.append("{}: {}".format(ex.__class__.__name__, str(ex)))

        log.info("Running headline NLG pipeline")
        try:
            headline_lang = "{}-head".format(language)
            headline = self.headline_pipeline.run((data,), headline_lang, prng_seed=self.registry.get("seed"))[0]
            log.info("Headline pipeline complete")
        except NoMessagesForSelectionException as ex:
            log.error("%s", ex)
            headline = get_error_message(language, "no-messages-for-selection")
            errors.append("NoMessagesForSelectionException")
        except NoInterestingMessagesException as ex:
            log.info("%s", ex)
            headline = get_error_message(language, "no-interesting-messages-for-selection")
            errors.append("NoInterestingMessagesException")
        except Exception as ex:
            log.exception("%s", ex)
            headline = get_error_message(language, "general-error")
            errors.append("{}: {}".format(ex.__class__.__name__, str(ex)))

        return headline, body, max_score, errors

    def _set_seed(self, seed_val: Optional[int] = None) -> None:
        log.info("Selecting seed for NLG pipeline")
        if not seed_val:
            seed_val = random.randint(1, 10000000)
            log.info("No preset seed, using random seed {}".format(seed_val))
        else:
            log.info("Using preset seed {}".format(seed_val))
        self.registry.register("seed", seed_val)

    def get_languages(self) -> List[str]:
        return list(self.registry.get("templates").keys())
