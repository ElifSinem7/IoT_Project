"""
MQTT Subscriber for Air Quality Monitoring System
Windows-compatible async implementation using aiomqtt
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import aiomqtt  # type: ignore
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Measurement
from .config import settings

logger = logging.getLogger(__name__)


class MQTTSubscriber:
    def __init__(self):
        self.broker = settings.MQTT_BROKER
        self.port = settings.MQTT_PORT
        self.topic = f"{settings.MQTT_TOPIC_PREFIX}+/data"  # Wildcard: tüm device'lar
        self.client: Optional[aiomqtt.Client] = None
        self.running = False
        self._reconnect_interval = 5

    async def process_message(self, message: aiomqtt.Message):
        """Process incoming MQTT message and save to database"""
        try:
            # Parse JSON payload
            payload = json.loads(message.payload.decode())
            logger.info(f"📥 MQTT Message: {payload}")

            # ✅ Gateway JSON mapping - support both formats
            device_id = payload.get("id") or payload.get("device_id", "unknown")
            
            # Timestamp
            ts_raw = payload.get("ts")  # Gateway ts (seconds since boot)
            ts_ms = payload.get("ts_ms")
            
            # Convert timestamp
            if ts_ms:
                ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            elif ts_raw:
                # Gateway timestamp - use current time instead
                ts = datetime.now(timezone.utc)
            else:
                ts = datetime.now(timezone.utc)

            # ✅ Gateway field mapping - support both formats
            # Temperature: Gateway sends "t" as x10 (234 = 23.4°C)
            temp_c = None
            if payload.get("t") is not None:
                temp_c = payload.get("t") / 10.0
            elif payload.get("temp_c") is not None:
                temp_c = payload.get("temp_c")
            
            # Humidity: Gateway sends "h" as x10 (291 = 29.1%)
            hum_rh = None
            if payload.get("h") is not None:
                hum_rh = payload.get("h") / 10.0
            elif payload.get("hum_rh") is not None:
                hum_rh = payload.get("hum_rh")
            
            # Pressure: Gateway sends "p" directly
            pressure_hpa = payload.get("p") or payload.get("pressure_hpa") or payload.get("press_hpa")
            
            # TVOC: Gateway sends "v"
            tvoc_ppb = payload.get("v") if payload.get("v") is not None else payload.get("tvoc_ppb")
            
            # eCO2: Gateway sends "e"
            eco2_ppm = payload.get("e") if payload.get("e") is not None else payload.get("eco2_ppm")
            
            # Score: Gateway sends "s"
            aq_score = payload.get("s") if payload.get("s") is not None else payload.get("aq_score")
            
            # Predictions: Gateway sends "pe" and "pv"
            pred_eco2_60m = payload.get("pe") if payload.get("pe") is not None else payload.get("pred_eco2_60m")
            pred_tvoc_60m = payload.get("pv") if payload.get("pv") is not None else payload.get("pred_tvoc_60m")
            
            # Anomalies: Gateway sends "ae" and "av"
            anom_eco2 = payload.get("ae", False) or payload.get("anom_eco2", False)
            anom_tvoc = payload.get("av", False) or payload.get("anom_tvoc", False)
            
            # Delta alert: Gateway sends "da"
            alert = payload.get("da", False) or payload.get("alert", False) or payload.get("delta_alert", False)
            
            # ✅ CRITICAL: Status - Gateway sends "st"
            status = payload.get("st") or payload.get("status", "NORMAL")
            
            # Frame counter: Gateway sends "fc"
            frame_counter = payload.get("fc")

            # Create measurement
            measurement = Measurement(
                device_id=device_id,
                ts=ts,
                temp_c=temp_c,
                hum_rh=hum_rh,
                pressure_hpa=pressure_hpa,
                tvoc_ppb=tvoc_ppb,
                eco2_ppm=eco2_ppm,
                rssi=payload.get("rssi"),
                snr=payload.get("snr"),
                aq_score=aq_score,
                pred_eco2_60m=pred_eco2_60m,
                pred_tvoc_60m=pred_tvoc_60m,
                anom_eco2=anom_eco2,
                anom_tvoc=anom_tvoc,
                alert=alert,
                status=status,
                sample_ms=payload.get("sample_ms"),
                frame_counter=frame_counter
            )

            # Save to database
            db = SessionLocal()
            try:
                db.add(measurement)
                db.commit()
                db.refresh(measurement)
                logger.info(f"✅ Saved to DB: device={device_id} status={measurement.status} eco2={measurement.eco2_ppm} tvoc={measurement.tvoc_ppb}")
            finally:
                db.close()

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)

    async def run(self):
        """Main MQTT subscriber loop with graceful shutdown"""
        logger.info(f"🔄 Starting MQTT subscriber: {self.broker}:{self.port}")
        logger.info(f"📡 Subscribing to: {self.topic}")
        
        self.running = True

        while self.running:
            try:
                async with aiomqtt.Client(
                    hostname=self.broker,
                    port=self.port,
                    keepalive=60
                ) as client:
                    await client.subscribe(self.topic)
                    logger.info(f"✅ MQTT connected and subscribed to {self.topic}")

                    async for message in client.messages:
                        if not self.running:
                            logger.info("🛑 Stopping MQTT message loop...")
                            break
                        await self.process_message(message)

            except asyncio.CancelledError:
                logger.info("🛑 MQTT task cancelled")
                self.running = False
                break
            except aiomqtt.MqttError as e:
                if self.running:  # Only reconnect if we're still supposed to be running
                    logger.error(f"❌ MQTT connection error: {e}")
                    logger.info(f"🔄 Reconnecting in {self._reconnect_interval} seconds...")
                    await asyncio.sleep(self._reconnect_interval)
                else:
                    break
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Unexpected error: {e}", exc_info=True)
                    await asyncio.sleep(self._reconnect_interval)
                else:
                    break

        logger.info("✅ MQTT subscriber stopped gracefully")

    async def stop(self):
        """Gracefully stop the MQTT subscriber"""
        logger.info("🛑 Stopping MQTT subscriber...")
        self.running = False


# Global subscriber instance
mqtt_subscriber = MQTTSubscriber()


async def start_mqtt_subscriber():
    """
    Start the MQTT subscriber task
    This function is called from main.py lifespan
    """
    try:
        await mqtt_subscriber.run()
    except asyncio.CancelledError:
        await mqtt_subscriber.stop()
        raise