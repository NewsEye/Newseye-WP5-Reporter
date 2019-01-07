from numpy.random import RandomState

import logging
log = logging.getLogger('root')


class NLGPipeline(object):

    def __init__(self, registry, *components):
        self._registry = registry
        self._components = components

    @property
    def registry(self):
        return self._registry

    @property
    def components(self):
        return self._components

    def run(self, initial_inputs, language, prng_seed=None):
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
                log.error("Exception occured while running with initial inputs {}".format(initial_inputs))
                log.exception(ex)
                raise
            args = output
        log.info("NLG Pipeline completed")
        return output


class NLGPipelineComponent(object):

    def __str__(self):
        return str(self.__class__.__name__)
