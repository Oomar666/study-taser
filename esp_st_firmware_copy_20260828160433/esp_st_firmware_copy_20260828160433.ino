/*
 * ==============================================================================
 * Project: Study Taser - ESP32-S3 Hardware Actuator Firmware (Standalone Wi-Fi)
 * Board:   ESP32-S3-DevKit
 * Target:  5V 1-Channel Low-Level Trigger Relay & Active Buzzer
 *
 * HARDWARE CONFIGURATION:
 *   - RELAY_PIN  : GPIO 0 (5V Low-Level Trigger Relay, Active LOW, Open-Drain)
 *   - BUZZER_PIN : GPIO 6 (Active High Buzzer, Active HIGH)
 *
 * WI-FI CONFIGURATION:
 *   - SSID     : "Oomar"
 *   - Password : "Oomar200632571"
 *   - mDNS Hostname: http://studytaser.local
 * ==============================================================================
 */

#include <WiFi.h>
#include <ESPmDNS.h>

// --- Wi-Fi Credentials ---
const char* ssid     = "Oomar";
const char* password = "Oomar200632571";

// --- Hardware Pin Definitions ---
const int RELAY_PIN  = 0;  // GPIO 0 for 5V Relay
const int BUZZER_PIN = 6;  // GPIO 6 for Buzzer

// --- Web Server on Port 80 ---
WiFiServer server(80);

// --- Communication & Safety Configuration ---
const unsigned long BAUD_RATE = 115200;
const unsigned long SAFETY_TIMEOUT_MS = 5000; // Auto-turn off if triggered without heartbeat
unsigned long lastTriggerTime = 0;
bool isSystemActive = false;

// --- Helper Functions to Control Actuators ---
void setActuators(bool turnOn) {
    if (turnOn) {
        // Open-Drain Low-Level Trigger Relay: LOW turns ON 5V relay
        digitalWrite(RELAY_PIN, LOW);
        // Active High Buzzer: HIGH turns ON buzzer
        digitalWrite(BUZZER_PIN, HIGH);

        isSystemActive = true;
        lastTriggerTime = millis();
    } else {
        // Open-Drain: HIGH floats pin, turning OFF 5V relay cleanly
        digitalWrite(RELAY_PIN, HIGH);
        // Buzzer OFF
        digitalWrite(BUZZER_PIN, LOW);

        isSystemActive = false;
    }
}

void connectToWiFi() {
    Serial.println("\n[Wi-Fi] Initializing Wi-Fi connection...");
    
    // Explicitly set Wi-Fi station mode and disable sleep for maximum stability & zero packet lag
    WiFi.disconnect(true);
    delay(100);
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false); // Disables Wi-Fi power saving to avoid dropped TCP packets

    WiFi.begin(ssid, password);
    Serial.print("[Wi-Fi] Connecting to Network SSID: ");
    Serial.println(ssid);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[Wi-Fi] SUCCESS! Connected to Wi-Fi.");
        Serial.print("[Wi-Fi] ESP32 IP Address: ");
        Serial.println(WiFi.localIP());
        Serial.print("[Wi-Fi] Signal Strength (RSSI): ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");

        // Start mDNS responder (allows connection via http://studytaser.local)
        if (MDNS.begin("studytaser")) {
            Serial.println("[mDNS] Responder started. Hostname: http://studytaser.local");
        }
    } else {
        Serial.println("\n[Wi-Fi] WARNING: Failed to connect within timeout.");
        Serial.println("[Wi-Fi] Retrying background connection...");
    }
}

void handleHttpClient(WiFiClient& client) {
    unsigned long waitStart = millis();
    while (!client.available() && (millis() - waitStart < 500)) {
        delay(1);
    }

    String requestLine = "";
    while (client.connected() && client.available()) {
        char c = client.read();
        if (c == '\n') break;
        if (c != '\r') requestLine += c;
    }

    if (requestLine.length() > 0) {
        Serial.print("[HTTP Request] ");
        Serial.println(requestLine);
    }

    if (requestLine.indexOf("GET /on") >= 0) {
        setActuators(true);
        Serial.println(" -> RELAY & BUZZER ACTIVATED (ON)");
        client.println("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\nON");
    } 
    else if (requestLine.indexOf("GET /off") >= 0) {
        setActuators(false);
        Serial.println(" -> RELAY & BUZZER DEACTIVATED (OFF)");
        client.println("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\nOFF");
    } 
    else if (requestLine.indexOf("GET /status") >= 0) {
        String statusJson = "{\"active\":" + String(isSystemActive ? "true" : "false") + "}";
        client.println("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n" + statusJson);
    } 
    else {
        client.println("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n404 Not Found");
    }

    delay(1);
    client.stop();
}

void setup() {
    Serial.begin(BAUD_RATE);
    delay(500);

    Serial.println("\n==================================================");
    Serial.println("  ESP32-S3 Study Taser Standalone Wi-Fi Firmware");
    Serial.println("==================================================");

    // Configure Pin Modes
    // CRITICAL: OPEN_DRAIN mode for RELAY_PIN (GPIO 0) prevents 3.3V vs 5V logic leakage
    pinMode(RELAY_PIN, OUTPUT_OPEN_DRAIN);
    pinMode(BUZZER_PIN, OUTPUT);

    // Initial default state: ALL OFF
    setActuators(false);

    // Connect to Wi-Fi
    connectToWiFi();

    // Start Web Server
    server.begin();
    Serial.println("[HTTP Server] Server listening on port 80.");
}

void loop() {
    // 1. Handle incoming Wi-Fi HTTP Clients
    WiFiClient client = server.available();
    if (client) {
        handleHttpClient(client);
    }

    // 2. Handle incoming USB Serial byte commands as fallback ('1' = ON, '0' = OFF)
    while (Serial.available() > 0) {
        char cmd = Serial.read();
        if (cmd == '1') {
            setActuators(true);
            Serial.println("[Serial CMD] -> RELAY & BUZZER ON");
        } else if (cmd == '0') {
            setActuators(false);
            Serial.println("[Serial CMD] -> RELAY & BUZZER OFF");
        }
    }

    // 3. Safety Watchdog Timeout: Auto turn off if connection drops while active
    if (isSystemActive && (millis() - lastTriggerTime > SAFETY_TIMEOUT_MS)) {
        Serial.println("[Watchdog] Safety timeout reached without heartbeat! Turning off actuators.");
        setActuators(false);
    }

    // 4. Auto Wi-Fi Reconnect Monitor
    static unsigned long lastWiFiCheck = 0;
    if (millis() - lastWiFiCheck > 10000) {
        lastWiFiCheck = millis();
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("[Wi-Fi] Disconnected! Attempting background reconnect...");
            WiFi.reconnect();
        }
    }

    delay(2);
}