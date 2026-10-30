# Alexa skill backend for smart-object

AWS Lambda backend for an Alexa skill (Alexa Skills Kit SDK for Python) that controls the ESP32 `smart-object` through its AWS IoT Core Device Shadow.

## Intents

| Intent       | Action                                                        | Response                    |
|--------------|---------------------------------------------------------------|-----------------------------|
| `TurnOnLed`  | Sets `state.desired.built-in-led` to `1`                      | "Listo, encendí el LED."    |
| `TurnOffLed` | Sets `state.desired.built-in-led` to `0`                      | "Listo, apagué el LED."     |
| `LedState`   | Reads `state.reported.built-in-led`                           | "El LED está encendido/apagado." |
| `GetCounter` | Reads `state.reported.counter`                                | "El contador vale N."       |

The ESP32 firmware (`src/main.cpp`) subscribes to the shadow delta topic, so a change in `desired` turns the LED on or off and the device reports the new state back. The device also reports `counter` every 10 seconds.

If the device hasn't reported a value yet, the skill says so. If the IoT call fails (for example, a missing permission), the skill says it couldn't reach the device and logs the error to CloudWatch.

## Configuration

The Lambda uses the classic (unnamed) shadow through the `boto3` `iot-data` client. `boto3` is included in the Lambda Python runtime, so it doesn't need to be in the deployment package.

Defaults match `include/config.h` and can be overridden with environment variables:

| Variable       | Default                                          |
|----------------|--------------------------------------------------|
| `THING_NAME`   | `smart-object`                                   |
| `IOT_ENDPOINT` | `YOUR_ENDPOINT-ats.iot.YOUR_REGION.amazonaws.com` |
| `IOT_REGION`   | `us-east-2`                                      |

## Setup

### 1. IAM permissions

Add this statement to the Lambda execution role (replace `<ACCOUNT_ID>` with your AWS account ID):

```json
{
  "Effect": "Allow",
  "Action": ["iot:GetThingShadow", "iot:UpdateThingShadow"],
  "Resource": "arn:aws:iot:us-east-2:<ACCOUNT_ID>:thing/smart-object"
}
```

### 2. Interaction model

In the Alexa developer console, add the four intents (names must match exactly). Sample utterances:

- `TurnOnLed`: "enciende el led", "prende la luz", "enciende el led integrado"
- `TurnOffLed`: "apaga el led", "apaga la luz"
- `LedState`: "cómo está el led", "está encendido el led", "estado del led"
- `GetCounter`: "cuánto vale el contador", "dime el contador", "valor del contador"

Build the model after saving.

### 3. Deploy

Rebuild the deployment package with the dependencies in `package/` plus `lambda_function.py`, and upload it to the Lambda:

```sh
rm -f lambda_deployment.zip
(cd package && zip -r ../lambda_deployment.zip .)
zip lambda_deployment.zip lambda_function.py
```
