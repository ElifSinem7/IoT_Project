## LoRa Packet Format

| Field       | Type   |
|------------|--------|
| device_id  | string |
| timestamp  | uint32 |
| temp_c     | float  |
| hum_rh     | float  |
| tvoc_ppb   | uint16 |
| eco2_ppm   | uint16 |
| rssi       | int8   |

Packets are encoded in a lightweight binary or JSON format
depending on node configuration.
