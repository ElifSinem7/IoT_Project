from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from .models import Measurement
from .config import settings


# =========================================================
# DATA STRUCTURES
# =========================================================

@dataclass
class AlertResult:
    score: float                    # 0..100
    status: str                     # OK / WARN / HIGH
    tvoc_increase_pct: Optional[float]
    eco2_increase_pct: Optional[float]


@dataclass
class TestRangeResult:
    status: str                     # NORMAL / HIGH
    violations: List[str]           # which values broke range


# =========================================================
# BASELINE / TREND-BASED ALERTING (PRODUCTION LOGIC)
# =========================================================

def _pct_increase(
    current: Optional[float],
    baseline: Optional[float]
) -> Optional[float]:
    if current is None or baseline is None:
        return None
    if baseline <= 0:
        return None
    return ((current - baseline) / baseline) * 100.0


def compute_baseline(
    db: Session,
    device_id: str,
    now_ts: datetime,
    window_seconds: int
) -> tuple[Optional[float], Optional[float]]:
    """
    Returns (tvoc_baseline, eco2_baseline) as averages
    over the last `window_seconds`.
    """
    start = now_ts - timedelta(seconds=window_seconds)

    stmt = (
        select(Measurement)
        .where(Measurement.device_id == device_id)
        .where(Measurement.ts >= start)
        .where(Measurement.ts <= now_ts)
    )

    rows = db.execute(stmt).scalars().all()

    tvocs = [r.tvoc_ppb for r in rows if r.tvoc_ppb is not None]
    eco2s = [r.eco2_ppm for r in rows if r.eco2_ppm is not None]

    tvoc_base = (sum(tvocs) / len(tvocs)) if tvocs else None
    eco2_base = (sum(eco2s) / len(eco2s)) if eco2s else None

    return tvoc_base, eco2_base


def decide_status(
    tvoc_pct: Optional[float],
    eco2_pct: Optional[float]
) -> str:
    """
    Decide OK / WARN / HIGH based on percentage increase.
    We trigger based on whichever increases more.
    """
    vals = [v for v in (tvoc_pct, eco2_pct) if v is not None]
    if not vals:
        return "OK"

    peak = max(vals)
    if peak >= settings.HIGH_INCREASE_PCT:
        return "HIGH"
    if peak >= settings.WARN_INCREASE_PCT:
        return "WARN"
    return "OK"


def compute_score(
    tvoc_pct: Optional[float],
    eco2_pct: Optional[float]
) -> float:
    """
    Map increase percent to a demo-friendly 0..100 score.
    """
    vals = [v for v in (tvoc_pct, eco2_pct) if v is not None]
    if not vals:
        return 0.0

    peak = max(vals)
    if settings.HIGH_INCREASE_PCT <= 0:
        return 0.0

    scaled = (peak / settings.HIGH_INCREASE_PCT) * 80.0
    return float(min(max(scaled, 0.0), 100.0))


def evaluate_alert(
    db: Session,
    device_id: str,
    ts: datetime,
    tvoc_ppb: Optional[float],
    eco2_ppm: Optional[float]
) -> AlertResult:
    """
    PRODUCTION MODE:
    Baseline + percentage increase based alerting.
    """
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    tvoc_base, eco2_base = compute_baseline(
        db, device_id, ts, settings.BASELINE_SECONDS
    )

    tvoc_pct = _pct_increase(tvoc_ppb, tvoc_base)
    eco2_pct = _pct_increase(eco2_ppm, eco2_base)

    status = decide_status(tvoc_pct, eco2_pct)
    score = compute_score(tvoc_pct, eco2_pct)

    return AlertResult(
        score=score,
        status=status,
        tvoc_increase_pct=tvoc_pct,
        eco2_increase_pct=eco2_pct,
    )


# =========================================================
# TEST MODE – DAR ARALIK, HYSTERESIS’Lİ HIGH / NORMAL
# =========================================================

def evaluate_test_ranges(
    eco2_ppm: int,
    tvoc_ppb: int,
    prev_status: Optional[str]
) -> TestRangeResult:
    """
    TEST MODE:
    Very sensitive range-based HIGH / NORMAL decision.
    Designed for physical sensor testing and demos.
    """

    status = prev_status or "NORMAL"
    violations: List[str] = []

    # ---------- eCO2 ----------
    if status == "NORMAL":
        if (
            eco2_ppm < settings.ECO2_TEST_MIN
            or eco2_ppm > settings.ECO2_TEST_MAX
        ):
            status = "HIGH"
            violations.append("eco2_out_of_range")
    else:  # currently HIGH
        if (
            settings.ECO2_TEST_MIN + settings.ECO2_HYST
            <= eco2_ppm
            <= settings.ECO2_TEST_MAX - settings.ECO2_HYST
        ):
            status = "NORMAL"

    # ---------- TVOC ----------
    if status == "NORMAL":
        if (
            tvoc_ppb < settings.TVOC_TEST_MIN
            or tvoc_ppb > settings.TVOC_TEST_MAX
        ):
            status = "HIGH"
            violations.append("tvoc_out_of_range")
    else:
        if (
            settings.TVOC_TEST_MIN + settings.TVOC_HYST
            <= tvoc_ppb
            <= settings.TVOC_TEST_MAX - settings.TVOC_HYST
        ):
            status = "NORMAL"

    return TestRangeResult(
        status=status,
        violations=violations,
    )