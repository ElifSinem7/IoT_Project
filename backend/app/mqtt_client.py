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

    async def process_message(self, message: aiomqtt.Message):
        """Process incoming MQTT message and save to database"""
        try:
            # Parse JSON payload
            payload = json.loads(message.payload.decode())
            logger.info(f"📥 MQTT Message: {payload}")

            # Extract data
            device_id = payload.get("device_id", "unknown")
            ts_ms = payload.get("ts_ms")
            
            # Convert timestamp
            if ts_ms:
                ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            else:
                ts = datetime.now(timezone.utc)

            # Create measurement
            measurement = Measurement(
                device_id=device_id,
                ts=ts,
                temp_c=payload.get("temp_c"),
                hum_rh=payload.get("hum_rh"),
                pressure_hpa=payload.get("pressure_hpa") or payload.get("press_hpa"),  # Backend mapping
                tvoc_ppb=payload.get("tvoc_ppb"),
                eco2_ppm=payload.get("eco2_ppm"),
                rssi=payload.get("rssi"),
                snr=payload.get("snr"),
                aq_score=payload.get("aq_score"),
                pred_eco2_60m=payload.get("pred_eco2_60m"),
                pred_tvoc_60m=payload.get("pred_tvoc_60m"),
                anom_eco2=payload.get("anom_eco2", False),
                anom_tvoc=payload.get("anom_tvoc", False),
                alert=payload.get("alert") or payload.get("delta_alert", False),  # Backend mapping
                status=payload.get("status", "NORMAL"),
                sample_ms=payload.get("sample_ms"),
                frame_counter=payload.get("fc")
            )

            # Save to database
            db = SessionLocal()
            try:
                db.add(measurement)
                db.commit()
                db.refresh(measurement)
                logger.info(f"✅ Saved to DB: device={device_id} eco2={measurement.eco2_ppm} status={measurement.status}")
            finally:
                db.close()

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)

    async def run(self):
        """Main MQTT subscriber loop"""
        logger.info(f"🔄 Starting MQTT subscriber: {self.broker}:{self.port}")
        logger.info(f"📡 Subscribing to: {self.topic}")

        while True:
            try:
                async with aiomqtt.Client(
                    hostname=self.broker,
                    port=self.port,
                    keepalive=60
                ) as client:
                    await client.subscribe(self.topic)
                    logger.info(f"✅ MQTT connected and subscribed to {self.topic}")

                    async for message in client.messages:
                        await self.process_message(message)

            except aiomqtt.MqttError as e:
                logger.error(f"❌ MQTT connection error: {e}")
                logger.info("🔄 Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}", exc_info=True)
                await asyncio.sleep(5)


# Global subscriber instance
mqtt_subscriber = MQTTSubscriber()


async def start_mqtt_subscriber():
    """
    Start the MQTT subscriber task
    This function is called from main.py lifespan
    """
    await mqtt_subscriber.run()