from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class IngestPayload(BaseModel):
    device_id: str = Field(..., examples=["node-001"])
    ts: Optional[datetime] = Field(None, description="ISO timestamp; boşsa server UTC now kullanır")

    temp_c: Optional[float] = None
    hum_rh: Optional[float] = None
    pressure_hpa: Optional[float] = None

    tvoc_ppb: Optional[float] = None
    eco2_ppm: Optional[float] = None

    rssi: Optional[float] = None
    snr: Optional[float] = None

class IngestResponse(BaseModel):
    ok: bool
    id: int

class MeasurementOut(BaseModel):
    device_id: str
    ts: datetime
    temp_c: Optional[float] = None
    hum_rh: Optional[float] = None
    pressure_hpa: Optional[float] = None
    tvoc_ppb: Optional[float] = None
    eco2_ppm: Optional[float] = None
    rssi: Optional[float] = None
    snr: Optional[float] = None
    score: Optional[float] = None
    status: Optional[str] = None


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
    score: Optional[float] = None
    status: Optional[str] = None
    tvoc_ppb: Optional[float] = None
    eco2_ppm: Optional[float] = None

