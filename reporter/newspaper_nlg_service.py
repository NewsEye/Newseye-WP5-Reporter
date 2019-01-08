import gzip
import os
import pickle
from random import randint
from typing import Generator, Callable, TypeVar, List, Dict, Tuple, Optional

from reporter.core import Registry, NLGPipeline, NLGPipelineComponent, Template
from reporter.core import BodyDocumentPlanner, HeadlineDocumentPlanner
from reporter.core.templates.read_multiling import read_templates_file
from reporter.core import SlotRealizer
from reporter.core import TemplateSelector
from reporter.core import Aggregator
from reporter.core import BodyHTMLSurfaceRealizer, HeadlineHTMLSurfaceRealizer
from reporter.newspaper_named_entity_resolver import NewspaperEntityNameResolver
from reporter.newspaper_importance_allocator import NewspaperImportanceSelector
from reporter.newspaper_message_generator import NewspaperMessageGenerator, NoMessagesForSelectionException
from reporter.constants import ERRORS

import logging

log = logging.getLogger('root')


class NewspaperNlgService(object):

    def __init__(self, random_seed: int = None, force_cache_refresh: bool = False) -> None:
        """
        :param random_seed: seed for random number generation, for repeatability
        :param force_cache_refresh: forces the recreation of all caches, taking significant amounts of time
        """

        # New registry and result importer
        self.registry = Registry()

        # Templates
        self.registry.register(
            'templates',
            self._get_cached_or_compute(
                '../data/templates.cache',
                self._load_templates,
                force_cache_refresh=force_cache_refresh
            )
        )

        # PRNG seed
        self._set_seed(seed_val=random_seed)

        def _get_components(headline=False) -> Generator[NLGPipelineComponent]:
            # Put together the list of components
            # This varies depending on whether it's for headlines and whether we're using Omorphi
            yield NewspaperMessageGenerator()  # Don't expand facts for headlines!
            yield NewspaperImportanceSelector()
            yield HeadlineDocumentPlanner() if headline else BodyDocumentPlanner()
            yield TemplateSelector()
            yield Aggregator()
            yield SlotRealizer()
            yield NewspaperEntityNameResolver()
            yield HeadlineHTMLSurfaceRealizer() if headline else BodyHTMLSurfaceRealizer()

        log.info("Configuring Body NLG Pipeline")
        self.body_pipeline = NLGPipeline(self.registry, *_get_components())
        self.headline_pipeline = NLGPipeline(self.registry, *_get_components(headline=True))

    T = TypeVar('T')

    def _get_cached_or_compute(self, cache: str, compute: Callable[T], force_cache_refresh: bool = False,
                               relative_path: bool = True) -> T:
        if relative_path:
            cache = os.path.abspath(os.path.join(os.path.dirname(__file__), cache))
        if force_cache_refresh:
            log.info("force_cache_refresh is True, deleting previous cache from {}".format(cache))
            if os.path.exists(cache):
                os.remove(cache)
        if not os.path.exists(cache):
            log.info("No cache at {}, computing".format(cache))
            result = compute()
            with gzip.open(cache, 'wb') as f:
                pickle.dump(result, f)
            return result
        else:
            log.info("Found cache at {}, decompressing and loading".format(cache))
            with gzip.open(cache, 'rb') as f:
                return pickle.load(f)

    def _load_templates(self) -> Dict[str, Template]:
        log.info('Loading templates')
        return read_templates_file(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", "main.txt")))

    def run_pipeline(self, language: str, where: str, where_type: str) -> Tuple[str, str]:
        log.info("Running Body NLG pipeline: language={}, where={}, where_type={}".format(language, where, where_type))
        try:
            body = self.body_pipeline.run(
                (where, where_type),
                language,
                prng_seed=self.registry.get('seed'),
            )[0]
            log.info("Body pipeline complete")
        except NoMessagesForSelectionException as ex:
            log.error("%s", ex)
            body = ERRORS.get(language, {}).get("no-messages-for-selection", "Something went wrong.")
        except Exception as ex:
            log.error("%s", ex)
            body = ERRORS.get(language, {}).get("general-error", "Something went wrong.")

        log.info("Running headline NLG pipeline")
        try:
            headline_lang = "{}-head".format(language)
            headline = self.headline_pipeline.run(
                (where, where_type),
                headline_lang,
                prng_seed=self.registry.get('seed'),
            )[0]
            log.info("Headline pipeline complete")
        except Exception as ex:
            headline = where
            log.error("%s", ex)

        return headline, body

    def _set_seed(self, seed_val: Optional[int] = None) -> None:
        log.info("Selecting seed for NLG pipeline")
        if not seed_val:
            seed_val = randint(1, 10000000)
            log.info("No preset seed, using random seed {}".format(seed_val))
        else:
            log.info("Using preset seed {}".format(seed_val))
        self.registry.register('seed', seed_val)

    def get_languages(self) -> List[str]:
        return list(self.registry.get('templates').keys())


if __name__ == "__main__":
    print('This is not a standalone file. Please start the server.')
