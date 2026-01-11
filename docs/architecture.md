## System Architecture

The proposed system follows a layered Internet of Things (IoT) architecture
consisting of sensing, communication, and application layers.

Sensor nodes continuously measure environmental and air quality parameters
including temperature, humidity, pressure, TVOC, and eCO₂. Each node performs
basic preprocessing and anomaly detection at the edge, then transmits
compressed data packets via LoRa (433 MHz) using a point-to-point topology.

A central gateway receives LoRa packets from multiple sensor nodes and forwards
the validated data to the backend server over Wi-Fi using serial communication.
The gateway acts as a bridge between the low-power LoRa network and the IP-based
backend infrastructure.

The backend server stores incoming measurements in a structured database,
performs data validation and alert processing, and exposes RESTful APIs for
data retrieval. These APIs are consumed by the web-based dashboard to enable
real-time monitoring, historical analysis, and geospatial visualization.

This architecture enables:
- Low power consumption at sensor nodes
- Long-range and reliable communication using LoRa
- Scalable multi-node deployments
- Centralized data storage and processing
- Real-time visualization and anomaly detection
