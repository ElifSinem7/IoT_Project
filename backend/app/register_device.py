import requests
import json

# Backend ayarları
BACKEND_URL = "http://localhost:8000"
API_KEY = "know-the-air-you-breaathe-in"

# Kayıt edilecek cihaz bilgileri
DEVICE_INFO = {
    "device_id": "node-001",
    "name": "AGÜ Kampüs Sensör 1",
    "lat": 38.7225,  # Kayseri AGÜ koordinatları (yaklaşık)
    "lon": 35.4875,
    "city": "Kayseri",
    "district": "Melikgazi"
}

def register_device():
    """Cihazı backend'e kaydet"""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/devices/register",
            json=DEVICE_INFO,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Cihaz başarıyla kaydedildi!")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        elif response.status_code == 400:
            print("⚠️  Cihaz zaten kayıtlı")
        else:
            print(f"✗ Hata: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"✗ Bağlantı hatası: {e}")

if __name__ == "__main__":
    register_device()