import logging
from typing import Any, Optional, Union, List, Tuple

from numpy.random import RandomState

from reporter.core import Registry

log = logging.getLogger('root')


class NLGPipelineComponent(object):

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
        log.info("Initial inputs are: {}".format(initial_inputs))
        args = initial_inputs
        for component in self.components:
            log.info("Running component {}".format(component))
            try:
                output = component.run(self.registry, prng, language, *args)
            except Exception as ex:
                log.error("Exception occurred while running with initial inputs {}".format(initial_inputs))
                log.exception(ex)
                raise
            if not (args is list or args is tuple):
                output = (output,)
            args = output
        log.info("NLG Pipeline completed")
        return output
