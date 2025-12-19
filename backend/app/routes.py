from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from .database import get_db
from .config import settings
from .schemas import IngestPayload, IngestResponse, LatestResponse, MeasurementOut, HistoryResponse
from . import crud
from .schemas import AlertLatestResponse


router = APIRouter()

def require_api_key(x_api_key: str | None):
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@router.get("/health")
def health():
    return {"ok": True, "name": settings.APP_NAME}

@router.post("/ingest", response_model=IngestResponse)
def ingest(
    payload: IngestPayload,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None),
):
    require_api_key(x_api_key)
    m = crud.create_measurement(db, payload)
    return IngestResponse(ok=True, id=m.id)

@router.get("/latest", response_model=LatestResponse)
def latest(device_id: str = Query(...), db: Session = Depends(get_db)):
    m = crud.get_latest(db, device_id)
    if not m:
        return LatestResponse(found=False, data=None)

    out = MeasurementOut(
        device_id=m.device_id,
        ts=m.ts,
        temp_c=m.temp_c,
        hum_rh=m.hum_rh,
        pressure_hpa=m.pressure_hpa,
        tvoc_ppb=m.tvoc_ppb,
        eco2_ppm=m.eco2_ppm,
        rssi=m.rssi,
        snr=m.snr,
        score=m.score,   
        status=m.status     
    )

    return LatestResponse(found=True, data=out)


@router.get("/history", response_model=HistoryResponse)
def history(
    device_id: str = Query(...),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    items = crud.get_history(db, device_id, start, end, limit)
    out_items = [
        MeasurementOut(
        device_id=m.device_id, 
        ts=m.ts,
        temp_c=m.temp_c, 
        hum_rh=m.hum_rh, 
        pressure_hpa=m.pressure_hpa,
        tvoc_ppb=m.tvoc_ppb, 
        eco2_ppm=m.eco2_ppm,
        rssi=m.rssi, 
        snr=m.snr,
        score=m.score,
        status=m.status
        )
        for m in items
    ]
    return HistoryResponse(device_id=device_id, count=len(out_items), items=out_items)

@router.get("/alerts/latest", response_model=AlertLatestResponse)
def alerts_latest(device_id: str = Query(...), db: Session = Depends(get_db)):
    m = crud.get_latest(db, device_id)
    if not m:
        return AlertLatestResponse(found=False)

    return AlertLatestResponse(
        found=True,
        device_id=m.device_id,
        ts=m.ts,
        score=m.score,
        status=m.status,
        tvoc_ppb=m.tvoc_ppb,
        eco2_ppm=m.eco2_ppm,
    )

