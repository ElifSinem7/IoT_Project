# 🌬️ Know The Air You Breathe In

**Know The Air You Breathe In** is a low-cost, distributed air quality monitoring system
designed to detect air pollution events in industrial, educational, and indoor environments.

The system combines **IoT sensors**, **LoRa communication**, **edge intelligence**, and a
**web-based dashboard** to provide real-time and historical air quality insights.

---

## 🚀 System Architecture

- **Sensor Nodes (ESP32 / ESP8266)**
  - SGP30 (TVOC, eCO₂)
  - BME680 (Temperature, Humidity, Pressure)
  - LoRa RA-02 (SX1278)

- **Gateway**
  - Receives LoRa packets
  - Sends data to backend via Wi-Fi (HTTP)

- **Backend (FastAPI)**
  - Stores measurements
  - Provides REST API
  - Alarm & anomaly-ready architecture

- **Frontend Dashboard**
  - Real-time visualization
  - Historical graphs
  - Pollution alerts

---

## 🧪 Demo Scenario

A transparent air tunnel / box is used to simulate pollution:
- Smoke (match or cigarette) is introduced
- Sensor values increase in real time
- Dashboard displays **“Air Pollution: HIGH!”**

---

## 📂 Project Structure

- `firmware/` → ESP32 / ESP8266 code (PlatformIO)
- `backend/` → FastAPI + SQLite backend
- `frontend/` → Web dashboard (Vite + JS/React)
- `docs/` → Architecture, API, demo documentation

---

## ⚙️ Technologies

- ESP32 / ESP8266
- LoRa RA-02 (SX1278)
- FastAPI (Python)
- SQLite
- Vite + Web Dashboard
- TinyML (planned)

---

## 📌 Future Work

- TinyML-based anomaly detection (LSTM)
- Emission source localization (triangulation)
- Multi-node deployment
- Edge-based alerts

---

> “You cannot improve what you cannot measure.”
