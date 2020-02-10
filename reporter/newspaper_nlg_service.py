import gzip
import logging
import os
import pickle
import random
from typing import Callable, Dict, Iterable, List, Optional, TypeVar, Tuple

from reporter.constants import CONJUNCTIONS, get_error_message
from reporter.core import (
    Aggregator,
    BodyDocumentPlanner,
    HeadlineDocumentPlanner,
    NLGPipeline,
    NLGPipelineComponent,
    read_templates_file,
    Registry,
    SlotRealizer,
    Template,
    TemplateSelector,
)
from reporter.core.document_planner import NoInterestingMessagesException
from reporter.core.surface_realizer import (
    BodyHTMLListSurfaceRealizer,
    BodyHTMLSurfaceRealizer,
    BodyHTMLOrderedListSurfaceRealizer,
    HeadlineHTMLSurfaceRealizer,
)
from reporter.newspaper_importance_allocator import NewspaperImportanceSelector
from reporter.newspaper_message_generator import (
    NewspaperMessageGenerator,
    NoMessagesForSelectionException,
)
from reporter.newspaper_named_entity_resolver import NewspaperEntityNameResolver
from reporter.newspaper_slot_realizers import inject_realizers

log = logging.getLogger("root")


class NewspaperNlgService(object):

    # These are (re)initialized every time run_pipeline is called
    body_pipeline = None
    headline_pipeline = None

    def __init__(self, random_seed: int = None) -> None:
        """
        :param random_seed: seed for random number generation, for repeatability
        """

        # New registry and result importer
        self.registry = Registry()

        # Templates
        self.registry.register(
            "templates",
            self._get_cached_or_compute(
                "../data/templates.cache", self._load_templates, force_cache_refresh=True
            ),
        )
        self.registry.register("CONJUNCTIONS", CONJUNCTIONS)
        # PRNG seed
        self._set_seed(seed_val=random_seed)

        # SurfazeRealizers
        inject_realizers(self.registry)

    T = TypeVar("T")

    def _get_cached_or_compute(
        self,
        cache: str,
        compute: Callable[..., T],
        force_cache_refresh: bool = False,
        relative_path: bool = True,
    ) -> T:
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
        return read_templates_file(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", "main.txt"))
        )

    def _get_components(self, realizer: str) -> Iterable[NLGPipelineComponent]:
        # Put together the list of components
        # This varies depending on whether it's for headlines and whether we're using Omorphi
        yield NewspaperMessageGenerator()  # Don't expand facts for headlines!
        yield NewspaperImportanceSelector()
        yield HeadlineDocumentPlanner() if realizer == "headline" else BodyDocumentPlanner()
        yield TemplateSelector()
        yield Aggregator()
        yield SlotRealizer()
        yield NewspaperEntityNameResolver()
        if realizer == "headline":
            yield HeadlineHTMLSurfaceRealizer()
        elif realizer == "ol":
            yield BodyHTMLOrderedListSurfaceRealizer()
        elif realizer == "ul":
            yield BodyHTMLListSurfaceRealizer()
        else:
            yield BodyHTMLSurfaceRealizer()

    def run_pipeline(self, language: str, output_format: str, data: str) -> Tuple[str, str]:
        log.info("Configuring Body NLG Pipeline")
        self.body_pipeline = NLGPipeline(self.registry, *self._get_components(output_format))
        self.headline_pipeline = NLGPipeline(self.registry, *self._get_components("headline"))

        log.info("Running Body NLG pipeline: language={}".format(language))
        try:
            body = self.body_pipeline.run((data,), language, prng_seed=self.registry.get("seed"))
            log.info("Body pipeline complete")
        except NoMessagesForSelectionException as ex:
            log.error("%s", ex)
            body = get_error_message(language, "no-messages-for-selection")
        except NoInterestingMessagesException as ex:
            log.info("%s", ex)
            body = get_error_message(language, "no-interesting-messages-for-selection")
        except Exception as ex:
            log.exception("%s", ex)
            body = get_error_message(language, "general-error")

        log.info("Running headline NLG pipeline")
        try:
            headline_lang = "{}-head".format(language)
            headline = self.headline_pipeline.run(
                (data,), headline_lang, prng_seed=self.registry.get("seed")
            )
            log.info("Headline pipeline complete")
        except NoMessagesForSelectionException as ex:
            log.error("%s", ex)
            headline = get_error_message(language, "no-messages-for-selection")
        except NoInterestingMessagesException as ex:
            log.info("%s", ex)
            headline = get_error_message(language, "no-interesting-messages-for-selection")
        except Exception as ex:
            log.exception("%s", ex)
            headline = get_error_message(language, "general-error")

        return headline, body

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
