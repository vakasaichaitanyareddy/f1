"""
OpenF1 Upstream Streaming Manager.
Manages authenticated MQTT/WebSocket connection to mqtt.openf1.org,
handles topic subscriptions, message validation, deduplication, reconnects,
and routes normalized events into APEX GP LiveSessionManager.
"""

import asyncio
import json
import logging
import ssl
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable

from app.core.config import settings
from app.racing.models import DataStateEnum
from app.racing.schemas import LiveIncrementalUpdate
from app.providers.openf1 import OpenF1Provider

logger = logging.getLogger("apex_gp.upstream_streamer")

class OpenF1StreamManager:
    """
    Connects to OpenF1 upstream MQTT broker (mqtt.openf1.org:8883) or WebSocket gateway.
    Maintains connection health, ingestion lag, and operational metrics.
    """
    def __init__(self, provider: Optional[OpenF1Provider] = None, event_callback: Optional[Callable] = None):
        self.provider = provider or OpenF1Provider()
        self.event_callback = event_callback
        self.broker = settings.OPENF1_MQTT_BROKER
        self.port = settings.OPENF1_MQTT_PORT
        self.is_connected = False
        self.subscribed_topics: List[str] = []
        self.active_session_key: Optional[str] = None
        self.last_upstream_timestamp: Optional[datetime] = None
        self.last_normalized_timestamp: Optional[datetime] = None
        self.last_redis_update_timestamp: Optional[datetime] = None
        self.total_messages_received = 0
        self.total_duplicates_filtered = 0
        self.connection_status = "DISCONNECTED" # "CONNECTED", "CONNECTING", "DISCONNECTED", "CREDENTIALS_MISSING"
        self._mqtt_client = None
        self._seen_message_ids = set()
        self._loop_task: Optional[asyncio.Task] = None

    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns structured operational metrics and connection diagnostics without secrets."""
        now = datetime.now(timezone.utc)
        ingestion_lag_seconds = None
        if self.last_upstream_timestamp:
            ingestion_lag_seconds = round((now - self.last_upstream_timestamp).total_seconds(), 3)

        return {
            "upstream_provider": "OpenF1_MQTT_Stream",
            "connection_status": self.connection_status,
            "is_connected": self.is_connected,
            "broker": f"{self.broker}:{self.port}",
            "active_session_key": self.active_session_key,
            "subscribed_topics": self.subscribed_topics,
            "last_upstream_message_time": self.last_upstream_timestamp.isoformat() if self.last_upstream_timestamp else None,
            "last_normalized_event_time": self.last_normalized_timestamp.isoformat() if self.last_normalized_timestamp else None,
            "last_redis_update_time": self.last_redis_update_timestamp.isoformat() if self.last_redis_update_timestamp else None,
            "ingestion_lag_seconds": ingestion_lag_seconds,
            "total_messages_received": self.total_messages_received,
            "total_duplicates_filtered": self.total_duplicates_filtered,
            "has_credentials": bool(settings.OPENF1_USERNAME and settings.OPENF1_PASSWORD)
        }

    async def start_streaming(self, session_key: str):
        """Starts upstream streaming subscription for a specific session."""
        self.active_session_key = session_key
        token = await self.provider.get_access_token()
        if not token:
            logger.warning("No OpenF1 token available for streaming (credentials missing or upstream rejected).")
            self.connection_status = "CREDENTIALS_MISSING"
            return False

        self.connection_status = "CONNECTING"
        try:
            import paho.mqtt.client as mqtt

            def on_connect(client, userdata, flags, rc, properties=None):
                if rc == 0:
                    self.is_connected = True
                    self.connection_status = "CONNECTED"
                    logger.info("Successfully connected to OpenF1 MQTT broker.")
                    # Subscribe to required supported topics for active session
                    topics = [
                        "v1/position",
                        "v1/intervals",
                        "v1/laps",
                        "v1/pit",
                        "v1/stints",
                        "v1/location",
                        "v1/car_data",
                        "v1/weather",
                        "v1/race_control"
                    ]
                    for t in topics:
                        client.subscribe(t)
                    self.subscribed_topics = topics
                else:
                    self.is_connected = False
                    self.connection_status = f"CONNECTION_FAILED_RC_{rc}"

                    logger.error(f"OpenF1 MQTT connection failed with result code {rc}")

            def on_message(client, userdata, msg):
                self._handle_raw_message(msg.topic, msg.payload)

            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            username = settings.OPENF1_USERNAME or "apex-gp-service"
            client.username_pw_set(username=username, password=token)
            client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
            client.on_connect = on_connect
            client.on_message = on_message

            self._mqtt_client = client
            client.connect_async(self.broker, self.port, 60)
            client.loop_start()
            return True
        except Exception as e:
            self.connection_status = f"ERROR: {type(e).__name__}"
            logger.error(f"Failed to start OpenF1 MQTT streaming: {e}")
            return False

    def _handle_raw_message(self, topic: str, payload_bytes: bytes):
        """Validates, deduplicates, and processes an incoming MQTT message payload."""
        try:
            now = datetime.now(timezone.utc)
            self.last_upstream_timestamp = now
            self.total_messages_received += 1

            payload = json.loads(payload_bytes.decode("utf-8"))
            if not isinstance(payload, dict):
                return

            # Check if message is for our active session key
            msg_session_key = str(payload.get("session_key", ""))
            if self.active_session_key and msg_session_key and msg_session_key != str(self.active_session_key):
                return # Discard other sessions

            # Deduplication key based on topic + timestamp + driver_number
            dedup_id = f"{topic}:{payload.get('driver_number')}:{payload.get('date')}:{payload.get('lap_number')}"
            if dedup_id in self._seen_message_ids:
                self.total_duplicates_filtered += 1
                return

            self._seen_message_ids.add(dedup_id)
            # Cap dedup cache to 5000 items
            if len(self._seen_message_ids) > 5000:
                self._seen_message_ids.clear()

            self.last_normalized_timestamp = datetime.now(timezone.utc)

            # Route to callback if registered
            if self.event_callback:
                self.event_callback(topic, payload)
        except Exception as err:
            logger.warning(f"Error handling raw upstream message: {err}")

    def stop_streaming(self):
        """Stops upstream MQTT client."""
        if self._mqtt_client:
            try:
                self._mqtt_client.loop_stop()
                self._mqtt_client.disconnect()
            except Exception:
                pass
            self._mqtt_client = None
        self.is_connected = False
        self.connection_status = "DISCONNECTED"
        self.subscribed_topics = []

# Global OpenF1 stream manager instance
openf1_stream_manager = OpenF1StreamManager()
