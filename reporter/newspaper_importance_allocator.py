from reporter.core.pipeline import NLGPipelineComponent

import logging
log = logging.getLogger('root')


class NewspaperImportanceSelector(NLGPipelineComponent):
    def run(self, registry, random, language, messages):
        """
        Runs this pipeline component.
        """
        facts = messages
        scored_messages = self.score_importance(facts, registry)
        sorted_scored_messages = sorted(scored_messages, key=lambda x: float(x.score), reverse=True)
        return sorted_scored_messages,

    def score_importance(self, messages, registry):
        for msg in messages:
            msg.score = self.score_importance_single(msg, registry)
        return messages

    def score_importance_single(self, message, registry):
        return 1
