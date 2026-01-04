import requests
import time
import random
from datetime import datetime, timezone
from threading import Thread

BACKEND_URL = "http://localhost:8000"
API_KEY = "know-the-air-you-breaathe-in"

# Birden fazla cihaz tanımla
DEVICES = [
    {
        "device_id": "node-001",
        "name": "AGÜ Merkez Kampüs",
        "base_temp": 22.0,
        "base_hum": 50.0
    },
    {
        "device_id": "node-002", 
        "name": "AGÜ Mühendislik Fakültesi",
        "base_temp": 23.0,
        "base_hum": 45.0
    },
    {
        "device_id": "node-003",
        "name": "AGÜ Kütüphane",
        "base_temp": 21.0,
        "base_hum": 55.0
    }
]

def generate_sensor_data(device):
    """Her cihaz için farklı sensör verileri üret"""
    # Bazal değerler etrafında dalgalanma
    temp_variation = random.uniform(-2, 2)
    hum_variation = random.uniform(-5, 5)
    
    return {
        "device_id": device["device_id"],
        "ts": datetime.now(timezone.utc).isoformat(),
        "temp_c": round(device["base_temp"] + temp_variation, 2),
        "hum_rh": round(device["base_hum"] + hum_variation, 2),
        "pressure_hpa": round(random.uniform(1000.0, 1020.0), 2),
        "tvoc_ppb": round(random.uniform(0, 500), 2),
        "eco2_ppm": round(random.uniform(400, 1500), 2),
        "rssi": round(random.uniform(-80, -40), 2),
        "snr": round(random.uniform(5, 15), 2)
    }

def send_data_for_device(device):
    """Bir cihaz için sürekli veri gönder"""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    while True:
        data = generate_sensor_data(device)
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/ingest",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✓ {device['device_id']}: {data['temp_c']}°C, {data['hum_rh']}%")
            else:
                print(f"✗ {device['device_id']}: Hata {response.status_code}")
                
        except Exception as e:
            print(f"✗ {device['device_id']}: {e}")
        
        time.sleep(random.uniform(4, 6))  # 4-6 saniye arası rastgele bekleme

def main():
    print(f"🌡️  Çoklu sensör simülatörü başlatıldı")
    print(f"📡 Backend: {BACKEND_URL}")
    print(f"🔢 {len(DEVICES)} cihaz simüle ediliyor\n")
    
    # Her cihaz için ayrı thread başlat
    threads = []
    for device in DEVICES:
        thread = Thread(target=send_data_for_device, args=(device,))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Ana thread'i canlı tut
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Simülatör durduruluyor...")

if __name__ == "__main__":
    main()