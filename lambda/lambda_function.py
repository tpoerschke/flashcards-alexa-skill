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

from .utils import init_session_attributes_for_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BACKEND_BASE_URL = "https://c308d87f8482.ngrok.io"
USER_ID_FOR_TOKEN = "/users/exchange-token"
CATEGORIES_BY_USER = "/users/{uid}/categories"
FLASHCARDS_BY_CATEGORY  = "/categories/{cid}/flashcards"

GENERIC_ERROR_MESSAGE = "Leider ist ein unerwarteter Fehler aufgetreten. Versuche es später erneut."

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input: HandlerInput):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput):
        speak_output = "Willkommen zu Flashcards. Ich kann dich abfragen. Sage dazu einfach \"Starte einen Test\""

        session = handler_input.request_envelope.session
        # Der Access Token sollte immer vorhanden sein, da der Nutzer den Account ja verlinken muss
        headers = {'Authorization': 'Bearer ' + session.user.access_token}
        response = requests.get(BACKEND_BASE_URL + USER_ID_FOR_TOKEN, headers=headers)
        if !response.ok:
            return handler_input.response_builder.speak(GENERIC_ERROR_MESSAGE).response
            
        user_id = response.json["user_id"]
        init_session_attributes_for_user()      

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
    """Handler zum Starten eines Tests. Dazu wird die Kategorie angefordert."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CaptureCategoryIntent")(handler_input)

    def handle(self, handler_input):
        global flashcards
        # type: (HandlerInput) -> Response
        category_slot = handler_input.request_envelope.request.intent.slots["category_name"].value
        speak_output = "Diese Kategorie kann ich nicht finden."

        for category in categories:
            # Alexa versteht anstatt "Webtechnologien" meist " Web technologien"...
            # Daher muss hier eine komplexe Abfrage her
            cat_title = category["title"].lower()
            logger.info("Überprüfte Kategorie: "+ cat_title)
            logger.info("Erkannte Kategorie: "+ category_slot)
            logger.info("Mapping: "+ str(list(map(lambda part: True if part in cat_title else False, category_slot.split()))))
            user_input_is_category = all(map(lambda part: True if part in cat_title else False, category_slot.split()))
            if user_input_is_category:
                speak_output = "Alles klar, ich werde dich in der Kategorie " + category_slot + " testen."
                response = requests.get(BACKEND_BASE_URL + FLASHCARDS_BY_CATEGORY.format(cid=category["id"]))
                if not response.ok:
                    return handler_input.response_builder.speak(GENERIC_ERROR_MESSAGE).response 
                flashcards = response.json()   
                if len(flashcards) == 0:
                    speak_output += " Oh oh... Leider gibt es keine Karten in dieser Kategorie."
                else:
                    speak_output, ask_output = self.__start_test(speak_output);
                break

        response_builder = handler_input.response_builder.speak(speak_output)
        if test_started:
            response_builder = response_builder.ask(ask_output)

        return response_builder.response
    
    def __start_test(self, speak_output):
        global test_started, current_card
        current_card = 0
        test_started = True
        speak_output += " Los geht's. Hier kommt die erste Frage: " + flashcards[current_card]["front"]
        ask_output = flashcards[current_card]["front"]
        return speak_output, ask_output

class ShowCardBackIntentHandler(AbstractRequestHandler):
    """Handler zum Umdrehen einer Karte."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ShowCardBackIntent")(handler_input) and test_started

    def handle(self, handler_input):
        global current_card, test_started
        # type: (HandlerInput) -> Response
        ask_output = ""
        speak_output = "Okay, hier kommt die Antwort: " + flashcards[current_card]["back"]
        current_card += 1
        
        if current_card >= len(flashcards):
            speak_output += "Das war die letzte Frage. Bis dann."
            test_started = False
        else:
            speak_output += "Die nächste Frage lautet: " + flashcards[current_card]["front"]
            ask_output += flashcards[current_card]["front"]
        
        response_builder = handler_input.response_builder.speak(speak_output)
        if test_started:
            response_builder = response_builder.ask(speak_output)
        
        return response_builder.response

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

        speak_output = "Sorry, ich habe Schwierigkeiten, deine Anfrage zu verarbeite. Bitte versuche es erneut."

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
sb.add_request_handler(ShowCardBackIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()