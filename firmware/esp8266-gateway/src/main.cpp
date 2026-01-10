#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <LoRa.h>
#include <ArduinoJson.h>
#include <time.h>  // ✅ TIME LIBRARY

// ==================== PIN DEFINITIONS (ESP32 GATEWAY) ====================
#define LORA_SCK   18
#define LORA_MISO  19
#define LORA_MOSI  23
#define LORA_CS    27
#define LORA_RST   14
#define LORA_DIO0  26
#define LED_GREEN  32
#define LED_RED    33
#define BUZZER_PIN 25

// ==================== WIFI / MQTT ====================
const char* WIFI_SSID = "elif's";
const char* WIFI_PASSWORD = "elifsinem";

const char* MQTT_SERVER = "broker.emqx.io";
const int   MQTT_PORT   = 1883;
const char* MQTT_CLIENT_ID = "kayseri_gateway_esp32";

// Topics
const char* TOPIC_PREFIX = "kayseri/air_quality/";

// ✅ NTP SETTINGS
const char* NTP_SERVER = "pool.ntp.org";
const long  GMT_OFFSET_SEC = 3 * 3600;  // Türkiye: GMT+3
const int   DAYLIGHT_OFFSET_SEC = 0;     // Yaz saati uygulaması yok

// ==================== LORA SETTINGS ====================
#define LORA_FREQUENCY  433E6
#define LORA_BANDWIDTH  125E3
#define LORA_SF         7
#define LORA_SYNC_WORD  0x34

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ==================== TIME SYNC ====================
bool timeIsSynced = false;

// ✅ NTP TIME SYNC FUNCTION
void setupTime() {
  Serial.println("\n🕐 Syncing time with NTP...");
  
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);
  
  // Wait for time sync (max 10 seconds)
  int attempts = 0;
  time_t now = time(nullptr);
  while (now < 1000000000 && attempts < 20) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
    attempts++;
  }
  Serial.println();
  
  if (now > 1000000000) {
    timeIsSynced = true;
    Serial.println("✅ Time synced!");
    
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);
    Serial.printf("   Current time: %04d-%02d-%02d %02d:%02d:%02d\n",
                  timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                  timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
  } else {
    timeIsSynced = false;
    Serial.println("⚠️ Time sync failed! Will use relative timestamps.");
  }
}

// ✅ GET CURRENT UNIX TIMESTAMP
unsigned long getCurrentTimestamp() {
  if (timeIsSynced) {
    time_t now = time(nullptr);
    return (unsigned long)now;
  } else {
    // Fallback: return 0 to indicate invalid timestamp
    return 0;
  }
}

// ==================== BUZZER LATCH ====================
static bool buzzerLatched = false;

// ==================== LED & BUZZER CONTROL ====================
void setAlertIndicators(bool alertActive) {
  if (alertActive) {
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
    
    if (!buzzerLatched) {
      for (int i = 0; i < 3; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(100);
        digitalWrite(BUZZER_PIN, LOW);
        delay(100);
      }
      buzzerLatched = true;
      Serial.println("🚨 ALERT ACTIVE: Red LED + Buzzer");
    } else {
      Serial.println("🚨 ALERT CONTINUES: Red LED (buzzer latched)");
    }
  } else {
    digitalWrite(LED_RED, LOW);
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(BUZZER_PIN, LOW);
    buzzerLatched = false;
    
    Serial.println("✅ Normal status: Green LED");
  }
}

// ------------------- WiFi + MQTT -------------------
void setupWiFi() {
  Serial.printf("📶 Connecting to WiFi: %s\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(250);
    Serial.print(".");
    attempts++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("✅ WiFi connected!");
    Serial.printf("   IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("   RSSI: %d dBm\n", WiFi.RSSI());
    
    // ✅ SYNC TIME AFTER WIFI CONNECTION
    setupTime();
  } else {
    Serial.println("❌ WiFi connection failed! (LoRa RX works, but cannot send MQTT)");
  }
}

void connectMQTT() {
  if (WiFi.status() != WL_CONNECTED) return;
  if (mqttClient.connected()) return;

  Serial.print("🔄 Connecting to MQTT... ");
  if (mqttClient.connect(MQTT_CLIENT_ID)) {
    Serial.println("✅ OK");
  } else {
    Serial.printf("❌ FAIL rc=%d\n", mqttClient.state());
  }
}

// ==================== LoRa Setup ====================
void setupLoRa() {
  Serial.println("\n📡 Initializing LoRa...");

  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(LORA_FREQUENCY)) {
    Serial.println("❌ LoRa initialization failed!");
    Serial.println("   Check: VCC=3.3V, common GND, pins, antenna");
    while (1) delay(1000);
  }

  LoRa.setSpreadingFactor(LORA_SF);
  LoRa.setSignalBandwidth(LORA_BANDWIDTH);
  LoRa.setSyncWord(LORA_SYNC_WORD);
  LoRa.enableCrc();

  LoRa.receive();
  Serial.println("✅ LoRa ready (RX)");
  Serial.printf("   F: %.0f MHz | SF:%d | BW:%.0f kHz | SW:0x%02X\n",
                LORA_FREQUENCY / 1E6, LORA_SF, LORA_BANDWIDTH / 1E3, LORA_SYNC_WORD);
}

// ==================== Receive (FULL JSON) + Publish ====================
void receiveAndPublish() {
  int packetSize = LoRa.parsePacket();
  if (!packetSize) return;
  Serial.printf("✅ PACKET DETECTED size=%d\n", packetSize);

  String rx;
  rx.reserve(packetSize + 8);
  while (LoRa.available()) rx += (char)LoRa.read();

  int rssi = LoRa.packetRssi();
  float snr = LoRa.packetSnr();

  Serial.println("\n🔥 LoRa packet received (SHORT JSON):");
  Serial.println(rx);
  Serial.printf("RSSI=%d dBm | SNR=%.2f dB | bytes=%d\n", rssi, snr, packetSize);

  StaticJsonDocument<512> in;
  DeserializationError err = deserializeJson(in, rx);
  if (err) {
    Serial.print("❌ JSON parse error: ");
    Serial.println(err.c_str());
    return;
  }

  const char* deviceId = in["id"] | "unknown";
  bool deltaAlert = in["da"] | false;
  const char* statusStr = in["st"] | "NORMAL";
  
  float temp_c = in["t"].as<int>() / 10.0;
  float hum_rh = in["h"].as<int>() / 10.0;
  int press_hpa = in["p"] | 0;
  int eco2_ppm = in["e"] | 0;
  int tvoc_ppb = in["v"] | 0;

  setAlertIndicators(deltaAlert);

  StaticJsonDocument<640> out;
  out["device_id"] = deviceId;

  // ✅ FIX: USE REAL UNIX TIMESTAMP
  unsigned long currentTimestamp = getCurrentTimestamp();
  if (currentTimestamp > 0) {
    // Time is synced, use real timestamp
    out["ts_ms"] = currentTimestamp * 1000UL;  // Convert to milliseconds
    Serial.printf("⏰ Using synced timestamp: %lu (%s)\n", 
                  currentTimestamp, 
                  timeIsSynced ? "SYNCED" : "FALLBACK");
  } else {
    // Time not synced, send 0 to let backend generate timestamp
    out["ts_ms"] = 0;
    Serial.println("⚠️ Time not synced, backend will generate timestamp");
  }

  out["temp_c"] = temp_c;
  out["hum_rh"] = hum_rh;
  out["press_hpa"] = press_hpa;
  out["eco2_ppm"] = eco2_ppm;
  out["tvoc_ppb"] = tvoc_ppb;

  out["rssi"] = rssi;
  out["snr"]  = snr;

  out["aq_score"] = in["s"];
  out["pred_eco2_60m"] = in["pe"];
  out["pred_tvoc_60m"] = in["pv"];
  out["anom_eco2"] = in["ae"];
  out["anom_tvoc"] = in["av"];
  
  out["delta_alert"] = deltaAlert;
  out["status"] = statusStr;

  out["sample_ms"] = in["sm"];
  out["fc"] = in["fc"];

  Serial.printf("📊 STATUS=%s | DELTA_ALERT=%d | eCO2=%d | TVOC=%d\n", 
                statusStr, deltaAlert, eco2_ppm, tvoc_ppb);
  
  if (in.containsKey("pe")) {
    Serial.printf("🧠 TinyML | pred_eco2_60m=%d | pred_tvoc_60m=%d | anom_eco2=%d | anom_tvoc=%d\n",
                  (int)in["pe"], (int)in["pv"],
                  (int)in["ae"], (int)in["av"]);
  }

  char jsonOut[640];
  size_t n = serializeJson(out, jsonOut, sizeof(jsonOut));
  jsonOut[n] = '\0';

  Serial.print("[SHORT->LONG JSON->MQTT] ");
  Serial.println(jsonOut);

  if (WiFi.status() == WL_CONNECTED) connectMQTT();

  if (mqttClient.connected()) {
    String topic = String(TOPIC_PREFIX) + deviceId + "/data";
    bool ok = mqttClient.publish(topic.c_str(), jsonOut);
    Serial.printf("[MQTT] %s => %s\n", topic.c_str(), ok ? "OK" : "FAIL");

    if (deltaAlert) {
      String atopic = String(TOPIC_PREFIX) + deviceId + "/alert";
      mqttClient.publish(atopic.c_str(), jsonOut);
      Serial.printf("[MQTT] DELTA ALERT %s\n", atopic.c_str());
    }
    
    if (in["ae"] == true || in["av"] == true) {
      String anomTopic = String(TOPIC_PREFIX) + deviceId + "/anomaly";
      mqttClient.publish(anomTopic.c_str(), jsonOut);
      Serial.printf("[MQTT] ANOMALY DETECTED %s\n", anomTopic.c_str());
    }
  } else {
    Serial.println("⚠️ MQTT not connected (normal if no WiFi).");
  }
}

// ==================== SETUP / LOOP ====================
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n=== ESP32 LoRa->MQTT Gateway (SHORT JSON + TinyML + NTP) ===");

  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  
  Serial.println("✅ LED and Buzzer pins configured");

  setupWiFi();  // ✅ This now also calls setupTime()
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);

  setupLoRa();

  digitalWrite(LED_GREEN, HIGH);
  Serial.println("💚 Green LED active (startup - normal status)");

  Serial.println("🚀 Gateway ready. Listening for LoRa packets...");
  Serial.println("   - NTP time sync: ENABLED");
  Serial.println("   - Delta detection: LED/Buzzer trigger");
  Serial.println("   - TinyML data: 60-min predictions");
  Serial.println("   - Anomaly detection: Separate MQTT topic\n");
}

void loop() {
  receiveAndPublish();

  if (WiFi.status() == WL_CONNECTED) {
    if (!mqttClient.connected()) connectMQTT();
    mqttClient.loop();
  }

  delay(5);
}