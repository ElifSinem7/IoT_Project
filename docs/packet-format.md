## LoRa Packet Format

Each sensor node transmits measurement data to the gateway using a compact
LoRa packet structure optimized for low bandwidth and energy efficiency.

| Field        | Type    |
|-------------|---------|
| device_id   | string  |
| timestamp   | uint32  |
| temp_c      | float   |
| hum_rh      | float   |
| pressure_hpa| float   |
| tvoc_ppb    | uint16  |
| eco2_ppm    | uint16  |
| rssi        | int8    |
| snr         | float   |
| anomaly     | boolean |

The packet includes both environmental parameters and air quality indicators,
as well as communication quality metrics used for link analysis.

Packets are encoded in a lightweight binary format to minimize payload size
and transmission time. For debugging and testing purposes, the system can
optionally switch to JSON encoding at the gateway level.
