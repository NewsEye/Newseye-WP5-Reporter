from abc import ABC
import logging
from typing import Any, List, Optional, Tuple, Union

from numpy.random import RandomState

from .registry import Registry

log = logging.getLogger('root')


class NLGPipelineComponent(ABC):

    def __str__(self) -> str:
        return str(self.__class__.__name__)


class NLGPipeline(object):

    def __init__(self, registry: Registry, *components: NLGPipelineComponent) -> None:
        self._registry = registry
        self._components = components

    @property
    def registry(self) -> Registry:
        return self._registry

    @property
    def components(self) -> Tuple[NLGPipelineComponent]:
        return self._components

    def run(self, initial_inputs: Any, language: str, prng_seed: Optional[int] = None) -> Union[List[Any], Tuple[Any]]:
        log.info("Starting NLG pipeline")
        log.debug("PRNG seed is {}".format(prng_seed))
        prng = RandomState(prng_seed)
        log.info("First random is {}".format(prng.randint(1000000)))
        args = initial_inputs
        for component in self.components:
            log.info("Running component {}".format(component))
            try:
                output = component.run(self.registry, prng, language, *args)
            except Exception as ex:
                log.exception(ex)
                raise
            args = output
        log.info("NLG Pipeline completed")
        return output
