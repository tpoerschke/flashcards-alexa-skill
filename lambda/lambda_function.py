# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import requests
import yaml

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CONFIG = yaml.load(open("config.yml", "r"))

BACKEND_BASE_URL = CONFIG["base_url"]
CATEGORIES_BY_USER = "/users/{uid}/categories"
FLASHCARDS_BY_CATEGORY  = "/categories/{cid}/flashcards"

USER_NAME = "timpo"
USER_PASS = "timpo"
USER_ID = 3

GENERIC_ERROR_MESSAGE = "Leider ist ein unerwarteter Fehler aufgetreten. Versuche es später erneut."

categories = []
flashcards = []
current_card = 0
test_started = False

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        global categories
        # type: (HandlerInput) -> Response
        speak_output = "Willkommen zu Flashcards. Ich kann dich abfragen. Sage dazu einfach \"Starte einen Test\""

        response = requests.get(BACKEND_BASE_URL + CATEGORIES_BY_USER.format(uid=USER_ID))
        if response.ok:
            categories = response.json()
        else:
            return handler_input.response_builder.speak(GENERIC_ERROR_MESSAGE).response

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class StartTestIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("StartTestIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Okay, in welcher Kategorie soll ich dich abfragen?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CaptureCategoryIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CaptureCategoryIntent")(handler_input)

    def handle(self, handler_input):
        global flashcards
        # type: (HandlerInput) -> Response
        category_slot = handler_input.request_envelope.request.intent.slots["category_name"].value
        speak_output = "Diese Kategorie kann ich nicht finden."

        for category in categories:
            if category["title"].lower() == category_slot:
                speak_output = "Alles klar, ich werde dich in der Kategorie " + category_slot + " testen. Los geht's."
                response = requests.get(BACKEND_BASE_URL + FLASHCARDS_BY_CATEGORY.format(cid=category["id"]))
                if not response.ok:
                    return handler_input.response_builder.speak(GENERIC_ERROR_MESSAGE).response 
                flashcards = response.json()   
                speak_output = self.__start_test(speak_output);
                break

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )
    
    def __start_test(self, speak_output):
        global test_started, current_card
        current_card = 0
        test_started = True
        speak_output += " Hier kommt die erste Frage: " + flashcards[0].front
        return speak_output

class ShowCardBackIntentHandler(AbstractRequestHandler):
    """Handler zum Umdrehen einer Karte."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ShowCardBackIntent")(handler_input) && test_started

    def handle(self, handler_input):
        global current_card, test_started
        # type: (HandlerInput) -> Response
        category_slot = handler_input.request_envelope.request.intent.slots["category_name"].value
        speak_output = "Diese Kategorie kann ich nicht finden."

        for category in categories:
            if category["title"].lower() == category_slot:
                speak_output = "Alles klar, ich werde dich in der Kategorie " + category_slot + " testen. Los geht's"
                response = requests.get(BACKEND_BASE_URL + FLASHCARDS_BY_CATEGORY.format(cid=category["id"]))
                if not response.ok:
                    return handler_input.response_builder.speak(GENERIC_ERROR_MESSAGE).response 
                flashcards = response.json()    
                break

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(StartTestIntentHandler())
sb.add_request_handler(CaptureCategoryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()