from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from datetime import datetime, timezone
from .models import Measurement
from .schemas import IngestPayload
from .alerts import evaluate_alert


def create_measurement(db: Session, payload: IngestPayload) -> Measurement:
    ts = payload.ts or datetime.now(timezone.utc)
    m = Measurement(
        device_id=payload.device_id,
        ts=ts,
        temp_c=payload.temp_c,
        hum_rh=payload.hum_rh,
        pressure_hpa=payload.pressure_hpa,
        tvoc_ppb=payload.tvoc_ppb,
        eco2_ppm=payload.eco2_ppm,
        rssi=payload.rssi,
        snr=payload.snr,
        
    )
    alert = evaluate_alert(db, payload.device_id, ts, payload.tvoc_ppb, payload.eco2_ppm)
    m.score = alert.score
    m.status = alert.status

    db.add(m)
    db.commit()
    db.refresh(m)
    return m

def get_latest(db: Session, device_id: str) -> Measurement | None:
    stmt = select(Measurement).where(Measurement.device_id == device_id).order_by(desc(Measurement.ts)).limit(1)
    return db.execute(stmt).scalars().first()

def get_history(db: Session, device_id: str, start, end, limit: int) -> list[Measurement]:
    stmt = select(Measurement).where(Measurement.device_id == device_id)
    if start:
        stmt = stmt.where(Measurement.ts >= start)
    if end:
        stmt = stmt.where(Measurement.ts <= end)
    stmt = stmt.order_by(Measurement.ts.asc()).limit(limit)
    return list(db.execute(stmt).scalars().all())
