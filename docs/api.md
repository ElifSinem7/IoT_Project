## Backend API

### GET /health
Checks if the backend service is running.

---

### POST /api/ingest
Receives sensor measurements from the LoRa gateway and stores them in the database.

---

### GET /api/latest
Returns the latest measurement for each registered device.

---

### GET /api/history
Returns historical sensor data for visualization and analysis.

---

### GET /api/alerts/latest
Returns the most recent air quality alert.

---

### GET /api/alerts/history
Returns historical alert records.

---

### GET /api/devices
Lists all registered sensor devices.

---

### POST /api/devices/register
Registers a new sensor device with location information.

---

### GET /api/devices/{device_id}
Returns detailed information for a specific device.

---

### GET /api/locations/cities
Returns all cities where sensors are deployed.

---

### GET /api/locations/districts
Returns districts for a given city.

---

### GET /api/map/points
Returns sensor points for map markers and heatmap visualization.

---

### GET /
Root endpoint of the backend service.
