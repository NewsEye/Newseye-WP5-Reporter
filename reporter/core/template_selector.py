import logging
from functools import lru_cache
from random import Random
from typing import List, Optional, Tuple, Generator

from reporter.core import Registry, DocumentPlan, Message
from .pipeline import NLGPipelineComponent
from .template import DefaultTemplate, Template

log = logging.getLogger('root')

# If we're starting a new paragraph and haven't mentioned the location for more than this number of
# messages, say it again (if possible), even if it's not changed
LOC_IF_NOT_SINCE = 6


class TemplateSelector(NLGPipelineComponent):
    """
    Adds a matching Template to each Message in the DocumentPlan.

    """

    def run(self, registry: Registry, random: Random, language: str, document_plan: DocumentPlan,
            all_messages: List[Message]) -> DocumentPlan:
        """
        Run this pipeline component.
        """
        if log.isEnabledFor(logging.DEBUG):
            document_plan.print_tree()

        templates = registry.get('templates')[language]

        template_checker = TemplateMessageChecker(templates, all_messages)
        log.info("Selecting templates from {} templates".format(len(templates)))
        self._recurse(random, language, document_plan, all_messages, template_checker)

        return document_plan

    def _recurse(self, random: Random, language: str, this: DocumentPlan, all_messages: List[Message],
                 template_checker: 'TemplateMessageChecker', current_location: Optional[str] = None,
                 since_location: int = 0) -> Tuple[str, str]:
        """
        Recursively works through the tree, adding Templates to Messages.
        """
        # Check all children of this root
        for idx, child in enumerate(this.children):
            # Will result in an AttributeError if the child is not a Message
            try:
                # Check whether the location has changed and we therefore need to express the new one
                location_required = current_location is None or child.fact.where != current_location
                templates = list(template_checker.all_templates_for_message(child, location_required=location_required))
                if len(templates) == 0:
                    # If there are no templates, something's gone horribly wrong
                    # The document planner should have made sure this didn't happen, but the only thing we can
                    #  at this point is skip the fact
                    log.error("Found no templates to express {} (location required: {})".format(
                        child, location_required
                    ))
                else:
                    if idx == 0 and since_location > LOC_IF_NOT_SINCE:
                        # First message of par, haven't mentioned loc for a while
                        # Prefer locationed templates, but allow unlocationed if it's the only option
                        preferred_templates = [t for t in templates if t.expresses_location]
                        other_templates = [t for t in templates if not t.expresses_location]
                    else:
                        # If we've got templates with and templates without locations, prefer those without
                        preferred_templates = [t for t in templates if not t.expresses_location]
                        other_templates = [t for t in templates if t.expresses_location]
                    # If there are multiple possibilities, choose randomly
                    if len(preferred_templates):
                        random.shuffle(preferred_templates)
                        template = preferred_templates[0]
                    else:
                        random.shuffle(other_templates)
                        template = other_templates[0]
                    self._add_template_to_message(child, template, all_messages)

                    # Update the current location to the one we just expressed (or implicitly did)
                    current_location = child.fact.where
                    # If we explicitly expressed the location, reset the counter
                    if template.expresses_location:
                        since_location = 0
                    else:
                        since_location += 1
            except AttributeError:
                # This child is NOT a message and we should just recurse
                current_location, since_location = \
                    self._recurse(random, language, child, all_messages, template_checker,
                                  current_location=current_location, since_location=since_location)
        return current_location, since_location

    @staticmethod
    def _add_template_to_message(message: Message, template_original: Template, all_messages: List[Message]) -> None:
        """
        Adds a matching template to a message, also adding the facts used by the template to the message.

        :param message: The message to be fitted with a template
        :param template_original: The template to be added to the message.
        :param all_messages: Other available messages, some of which will be needed to match possible secondary rules
               in the template.
        :return: Nothing
        """
        template = template_original.copy()
        used_facts = template.fill(message, all_messages)
        if used_facts:
            log.debug("Successfully linked template to message")
        else:
            log.error("Chosen template '{}' for fact '{}' could not be used! "
                      "Falling back to default templates".format(template.display_template(), message.fact))
            template = DefaultTemplate("")
        message.template = template
        message.facts = used_facts


class TemplateMessageChecker(object):
    """
    Doesn't actually fill in templates, but just checks, for a given message (and a list of other available messages),
    whether there is a template that can be used to realise it.

    Init with templates taken from the registry for the relevant language.

    The checks are cached on message and location_required.

    """

    def __init__(self, templates: List[Template], all_messages: List[Message]) -> None:
        self.all_messages = all_messages
        self.templates = templates
        self._cache = {}

    @lru_cache(maxsize=1024)
    def exists_template_for_message(self, message: Message, location_required: bool = False) -> bool:
        """
        Check for templates that apply to the given message. To make things faster, we don't try to find
        all available templates, but return as soon as we find one.

        :param message:
        :param location_required: by default, allows templates with or without location. If location_required=True,
            only accept templates that explicitly express the message's location
        :return:
        """
        try:
            # Try getting the first template
            next(self.all_templates_for_message(message, location_required=location_required))
        except StopIteration:
            # No template found at all
            return False
        return True

    def all_templates_for_message(self, message: Message, location_required: bool = False) -> Generator[Template]:
        for template in self.templates:
            # If we need the location, only accept templates that express it
            if location_required and not template.expresses_location:
                continue
            # See if the template can express this message (with the help of the other available messages)
            if template.check(message, self.all_messages):
                # Got a matching template: this message can be expressed
                yield template
