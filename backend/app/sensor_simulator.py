import requests
import time
import random
from datetime import datetime, timezone
import json

# Backend ayarları
BACKEND_URL = "http://localhost:8000"  # Backend adresini buraya yaz
API_KEY = "know-the-air-you-breaathe-in"  # config.py'deki API_KEY ile aynı olmalı
DEVICE_ID = "node-001"  # Cihaz ID'si

def generate_sensor_data():
    """Sensör verilerini simüle et"""
    return {
        "device_id": DEVICE_ID,
        "ts": datetime.now(timezone.utc).isoformat(),
        "temp_c": round(random.uniform(18.0, 28.0), 2),
        "hum_rh": round(random.uniform(30.0, 70.0), 2),
        "pressure_hpa": round(random.uniform(1000.0, 1020.0), 2),
        "tvoc_ppb": round(random.uniform(0, 500), 2),
        "eco2_ppm": round(random.uniform(400, 1500), 2),
        "rssi": round(random.uniform(-80, -40), 2),
        "snr": round(random.uniform(5, 15), 2)
    }

def send_data():
    """Veriyi backend'e gönder"""
    data = generate_sensor_data()
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/ingest",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✓ Veri gönderildi: {datetime.now().strftime('%H:%M:%S')}")
            print(f"  Sıcaklık: {data['temp_c']}°C, Nem: {data['hum_rh']}%, TVOC: {data['tvoc_ppb']} ppb")
        else:
            print(f"✗ Hata: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"✗ Bağlantı hatası: {e}")

def main():
    print(f"🌡️  Sensör simülatörü başlatıldı ({DEVICE_ID})")
    print(f"📡 Backend: {BACKEND_URL}")
    print(f"⏱️  Her 5 saniyede bir veri gönderilecek\n")
    
    while True:
        send_data()
        time.sleep(5)  # 5 saniye bekle

if __name__ == "__main__":
    main()