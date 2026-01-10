from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class IngestPayload(BaseModel):
    device_id: str = Field(..., examples=["node-001"])
    ts: Optional[datetime] = Field(None, description="ISO timestamp; if empty, server uses UTC now")

    temp_c: Optional[float] = None
    hum_rh: Optional[float] = None
    pressure_hpa: Optional[float] = None

    tvoc_ppb: Optional[int] = None
    eco2_ppm: Optional[int] = None

    rssi: Optional[int] = None
    snr: Optional[float] = None

class IngestResponse(BaseModel):
    ok: bool
    id: int

class MeasurementOut(BaseModel):
    device_id: str
    ts: datetime
    
    # Sensor data
    temp_c: Optional[float] = None
    hum_rh: Optional[float] = None
    pressure_hpa: Optional[float] = None
    tvoc_ppb: Optional[int] = None
    eco2_ppm: Optional[int] = None
    
    # LoRa metrics
    rssi: Optional[int] = None
    snr: Optional[float] = None
    
    # Air quality score
    aq_score: Optional[int] = None
    
    # TinyML predictions
    pred_eco2_60m: Optional[int] = None
    pred_tvoc_60m: Optional[int] = None
    
    # Anomaly detection
    anom_eco2: Optional[bool] = None
    anom_tvoc: Optional[bool] = None
    
    # Alert & Status
    alert: bool = False
    status: Optional[str] = None
    
    # Metadata
    sample_ms: Optional[int] = None
    frame_counter: Optional[int] = None


class LatestResponse(BaseModel):
    found: bool
    data: Optional[MeasurementOut] = None

class HistoryResponse(BaseModel):
    device_id: str
    count: int
    items: List[MeasurementOut]

class AlertLatestResponse(BaseModel):
    found: bool
    device_id: Optional[str] = None
    ts: Optional[datetime] = None
    aq_score: Optional[int] = None
    status: Optional[str] = None
    tvoc_ppb: Optional[int] = None
    eco2_ppm: Optional[int] = None
    alert: Optional[bool] = None


# ✅ EKSIK SCHEMA - YENİ EKLENDİ
class AlertHistoryResponse(BaseModel):
    """Alert history response"""
    device_id: str
    count: int
    items: List[MeasurementOut]


# ==================== Map Schemas ====================

class DeviceCreate(BaseModel):
    """Create new device"""
    device_id: str
    name: str
    lat: float
    lon: float
    city: str
    district: str


class DeviceOut(BaseModel):
    """Device information"""
    device_id: str
    name: str
    lat: float
    lon: float
    city: str
    district: str
    created_at: datetime


class MapPoint(BaseModel):
    """Point on the map"""
    id: str
    device_id: str
    name: str
    lat: float
    lon: float
    city: str
    district: str
    tvoc_ppb: Optional[int] = None
    eco2_ppm: Optional[int] = None
    temperature: Optional[float] = None  # comes as temp_c
    humidity: Optional[float] = None     # comes as hum_rh
    pressure: Optional[float] = None     # comes as pressure_hpa
    score: Optional[int] = None          # ✅ routes.py compatibility (maps from aq_score)
    status: Optional[str] = None
    last_update: Optional[datetime] = None


class MapPointsResponse(BaseModel):
    """Map points response"""
    points: List[MapPoint]


class CitiesResponse(BaseModel):
    """City list response"""
    cities: List[str]


class DistrictsResponse(BaseModel):
    """District list response"""
    city: str
    districts: List[str]

# Alert History Response
class AlertHistoryResponse(BaseModel):
    device_id: str
    count: int
    items: List[MeasurementOut]