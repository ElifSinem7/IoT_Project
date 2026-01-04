from sqlalchemy import Integer, Float, String, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from .database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Device(Base):
    """Sensor cihazları - konum ve meta bilgiler"""
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256))
    
    # Konum bilgileri (harita için)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    city: Mapped[str] = mapped_column(String(128), index=True)
    district: Mapped[str] = mapped_column(String(128), index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=utc_now)

    # ==================== SENSOR DATA ====================
    temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    hum_rh: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_hpa: Mapped[float | None] = mapped_column(Float, nullable=True)

    tvoc_ppb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eco2_ppm: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ==================== LORA METRICS ====================
    rssi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snr: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ==================== AIR QUALITY SCORE ====================
    aq_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100

    # ==================== TINYML PREDICTIONS ====================
    pred_eco2_60m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pred_tvoc_60m: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ==================== ANOMALY DETECTION ====================
    anom_eco2: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    anom_tvoc: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # ==================== ALERT & STATUS ====================
    alert: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    status: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)  # NORMAL/WARN/HIGH

    # ==================== METADATA ====================
    sample_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frame_counter: Mapped[int | None] = mapped_column(Integer, nullable=True)


# Composite index for efficient queries
Index("ix_device_ts", Measurement.device_id, Measurement.ts)