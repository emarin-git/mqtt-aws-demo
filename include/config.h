#pragma once

// ============================================================
//  Archivo de configuración del proyecto mqtt-aws-demo
//  Modifique aquí todos los parámetros antes de compilar.
//  Los certificados y la clave privada van en secrets.h.
// ============================================================

// ---------- Red Wi-Fi ----------
#define WIFI_SSID          "YOUR_WIFI_SSID"
#define WIFI_PASSWORD      "YOUR_WIFI_PASSWORD"

// ---------- AWS IoT Core ----------
// Endpoint: AWS IoT > Settings > Device data endpoint
#define AWS_IOT_ENDPOINT   "YOUR_ENDPOINT-ats.iot.YOUR_REGION.amazonaws.com"
#define MQTT_PORT          8883
#define THING_NAME         "smart-object"  // también se usa como client ID MQTT
#define MQTT_BUFFER_SIZE   1024         // los mensajes del shadow superan los 256 bytes por defecto

// ---------- Tópicos ----------
#define TOPIC_SHADOW_UPDATE "$aws/things/" THING_NAME "/shadow/update"        // publica estado reportado
#define TOPIC_SHADOW_DELTA  "$aws/things/" THING_NAME "/shadow/update/delta"  // recibe cambios deseados

// ---------- LED interno ----------
#define LED_PIN            2      // LED azul de la ESP32 DOIT DevKit V1
#define LED_ACTIVE_LOW     false  // true si el LED enciende con nivel bajo (p. ej. ESP8266)
#define SHADOW_LED_KEY     "built-in-led"  // propiedad del shadow: 1 = encendido, 0 = apagado

// ---------- Contador ----------
#define SHADOW_COUNTER_KEY "counter"      // propiedad del shadow con el valor del contador

// ---------- Tiempos (ms) ----------
#define COUNTER_INTERVAL_MS     1000  // incremento del contador
#define REPORT_INTERVAL_MS     10000  // publicación del contador en el shadow
#define WIFI_RETRY_INTERVAL_MS  5000  // espera entre intentos de reconexión Wi-Fi
#define MQTT_RETRY_INTERVAL_MS  5000  // espera entre intentos de reconexión MQTT

// ---------- Depuración ----------
#define SERIAL_BAUD        115200
