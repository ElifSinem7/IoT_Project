## System Architecture

Sensor nodes continuously measure air quality parameters and transmit
compressed data packets via LoRa to a central gateway.

The gateway forwards these packets to a backend server over Wi-Fi.
The backend stores the data, performs validation, and exposes REST APIs
for visualization and analysis.

This architecture enables:
- Low power consumption
- Long-range communication
- Scalable multi-node deployments
- Centralized analysis and anomaly detection
