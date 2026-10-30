# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configuración de AWS IoT Core (debe coincidir con include/config.h del firmware).
THING_NAME = os.environ.get("THING_NAME", "smart-object")
IOT_ENDPOINT = os.environ.get("IOT_ENDPOINT", "YOUR_ENDPOINT-ats.iot.YOUR_REGION.amazonaws.com")
IOT_REGION = os.environ.get("IOT_REGION", "us-east-2")
SHADOW_LED_KEY = "built-in-led"
SHADOW_COUNTER_KEY = "counter"

iot_data = boto3.client("iot-data", region_name=IOT_REGION, endpoint_url="https://" + IOT_ENDPOINT)


def get_reported_state():
    """Devuelve state.reported del shadow clásico del Thing."""
    response = iot_data.get_thing_shadow(thingName=THING_NAME)
    shadow = json.loads(response["payload"].read())
    return shadow.get("state", {}).get("reported", {})


def set_desired_led(value):
    """Actualiza state.desired.built-in-led; el ESP32 lo recibe vía el tópico delta."""
    payload = {"state": {"desired": {SHADOW_LED_KEY: value}}}
    iot_data.update_thing_shadow(thingName=THING_NAME, payload=json.dumps(payload))


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        speak_output = ("Bienvenido. Puedes pedirme encender o apagar el LED, "
                        "preguntar su estado o el valor del contador. Qué quieres hacer?")

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class TurnOnLedIntentHandler(AbstractRequestHandler):
    """Handler for TurnOnLed Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("TurnOnLed")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            set_desired_led(1)
            speak_output = "Listo, encendí el LED."
        except ClientError as e:
            logger.error(e, exc_info=True)
            speak_output = "No pude comunicarme con el dispositivo."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Algo más?")
                .response
        )


class TurnOffLedIntentHandler(AbstractRequestHandler):
    """Handler for TurnOffLed Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("TurnOffLed")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            set_desired_led(0)
            speak_output = "Listo, apagué el LED."
        except ClientError as e:
            logger.error(e, exc_info=True)
            speak_output = "No pude comunicarme con el dispositivo."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Algo más?")
                .response
        )


class LedStateIntentHandler(AbstractRequestHandler):
    """Handler for LedState Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("LedState")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            led = get_reported_state().get(SHADOW_LED_KEY)
            if led is None:
                speak_output = "El dispositivo todavía no ha reportado el estado del LED."
            else:
                speak_output = "El LED está {}.".format("encendido" if led else "apagado")
        except ClientError as e:
            logger.error(e, exc_info=True)
            speak_output = "No pude obtener el estado del dispositivo."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Algo más?")
                .response
        )


class GetCounterIntentHandler(AbstractRequestHandler):
    """Handler for GetCounter Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GetCounter")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            counter = get_reported_state().get(SHADOW_COUNTER_KEY)
            if counter is None:
                speak_output = "El dispositivo todavía no ha reportado el contador."
            else:
                speak_output = "El contador vale {}.".format(counter)
        except ClientError as e:
            logger.error(e, exc_info=True)
            speak_output = "No pude obtener el estado del dispositivo."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Algo más?")
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = ("Puedes decir: enciende el LED, apaga el LED, "
                        "cómo está el LED, o cuánto vale el contador. Qué quieres hacer?")

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
sb.add_request_handler(TurnOnLedIntentHandler())
sb.add_request_handler(TurnOffLedIntentHandler())
sb.add_request_handler(LedStateIntentHandler())
sb.add_request_handler(GetCounterIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
