#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "config.h"
#include "secrets.h"

WiFiClientSecure wifiClient;
PubSubClient mqtt(wifiClient);

bool ledOn = false;
unsigned long counter = 0;
unsigned long lastIncrement = 0;
unsigned long lastReport = 0;
unsigned long lastWifiAttempt = 0;
unsigned long lastMqttAttempt = 0;

void setLed(bool on) {
  ledOn = on;
  digitalWrite(LED_PIN, (on != LED_ACTIVE_LOW) ? HIGH : LOW);
}

// Publica doc en el tópico de actualización del Device Shadow.
void publishShadow(JsonDocument &doc) {
  char buffer[128];
  serializeJson(doc, buffer, sizeof(buffer));
  mqtt.publish(TOPIC_SHADOW_UPDATE, buffer);
  Serial.printf("[Shadow] %s -> %s\n", TOPIC_SHADOW_UPDATE, buffer);
}

// Publica el estado actual del LED en state.reported del Device Shadow.
void reportLedState() {
  JsonDocument doc;
  doc["state"]["reported"][SHADOW_LED_KEY] = ledOn ? 1 : 0;
  publishShadow(doc);
}

// Publica el valor actual del contador en state.reported del Device Shadow.
void reportCounter() {
  JsonDocument doc;
  doc["state"]["reported"][SHADOW_COUNTER_KEY] = counter;
  publishShadow(doc);
}

void onMqttMessage(char *topic, byte *payload, unsigned int length) {
  Serial.printf("[MQTT] Mensaje en %s: %.*s\n", topic, length, (const char *)payload);

  if (strcmp(topic, TOPIC_SHADOW_DELTA) != 0) {
    return;
  }

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    Serial.printf("[Shadow] JSON inválido: %s\n", err.c_str());
    return;
  }

  JsonVariant led = doc["state"][SHADOW_LED_KEY];
  if (!led.is<int>()) {
    Serial.println("[Shadow] Delta sin " SHADOW_LED_KEY " (se espera 0 o 1)");
    return;
  }

  setLed(led.as<int>() != 0);
  Serial.printf("[LED] %s\n", ledOn ? "Encendido" : "Apagado");
  reportLedState();
}

// Gestiona la conexión Wi-Fi sin bloquear. Devuelve true si hay conexión.
bool ensureWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    return true;
  }

  unsigned long now = millis();
  if (lastWifiAttempt == 0 || now - lastWifiAttempt >= WIFI_RETRY_INTERVAL_MS) {
    lastWifiAttempt = now;
    Serial.printf("[WiFi] Conectando a %s...\n", WIFI_SSID);
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  }
  return false;
}

// Gestiona la conexión MQTT sin bloquear. Devuelve true si hay conexión.
bool ensureMqtt() {
  if (mqtt.connected()) {
    return true;
  }

  unsigned long now = millis();
  if (lastMqttAttempt != 0 && now - lastMqttAttempt < MQTT_RETRY_INTERVAL_MS) {
    return false;
  }
  lastMqttAttempt = now;

  Serial.printf("[MQTT] Conectando a %s:%d como %s...\n", AWS_IOT_ENDPOINT, MQTT_PORT, THING_NAME);

  if (!mqtt.connect(THING_NAME)) {
    Serial.printf("[MQTT] Fallo, estado=%d. Reintentando en %d ms\n", mqtt.state(), MQTT_RETRY_INTERVAL_MS);
    return false;
  }

  Serial.println("[MQTT] Conectado");
  mqtt.subscribe(TOPIC_SHADOW_DELTA);
  Serial.printf("[MQTT] Suscrito a %s\n", TOPIC_SHADOW_DELTA);
  reportLedState();
  return true;
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(100);

  pinMode(LED_PIN, OUTPUT);
  setLed(false);

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);

  wifiClient.setCACert(AWS_ROOT_CA);
  wifiClient.setCertificate(AWS_DEVICE_CERT);
  wifiClient.setPrivateKey(AWS_PRIVATE_KEY);

  mqtt.setServer(AWS_IOT_ENDPOINT, MQTT_PORT);
  mqtt.setBufferSize(MQTT_BUFFER_SIZE);
  mqtt.setCallback(onMqttMessage);
}

void loop() {
  static bool wifiWasConnected = false;

  bool wifiOk = ensureWifi();
  if (wifiOk && !wifiWasConnected) {
    Serial.printf("[WiFi] Conectado, IP: %s\n", WiFi.localIP().toString().c_str());
    lastMqttAttempt = 0;  // intentar MQTT de inmediato
  } else if (!wifiOk && wifiWasConnected) {
    Serial.println("[WiFi] Conexión perdida");
  }
  wifiWasConnected = wifiOk;

  if (wifiOk && ensureMqtt()) {
    mqtt.loop();
  }

  // El contador se incrementa cada segundo aunque no haya conexión;
  // se reporta al shadow cada REPORT_INTERVAL_MS cuando MQTT está disponible.
  unsigned long now = millis();
  if (now - lastIncrement >= COUNTER_INTERVAL_MS) {
    lastIncrement = now;
    counter++;
  }

  if (now - lastReport >= REPORT_INTERVAL_MS && mqtt.connected()) {
    lastReport = now;
    reportCounter();
  }
}
