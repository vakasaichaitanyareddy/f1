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

from collections import OrderedDict

logger = logging.getLogger("apex_gp.upstream_streamer")

class OpenF1StreamManager:
    """
    Connects to OpenF1 upstream MQTT broker (mqtt.openf1.org:8883) or WebSocket gateway.
    Maintains connection health, ingestion lag, event ordering, deduplication, and operational metrics.
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
        self.total_out_of_order_filtered = 0
        self.connection_status = "DISCONNECTED" # "CONNECTED", "CONNECTED_RECEIVING", "CONNECTED_IDLE", "CONNECTING", "DISCONNECTED", "CREDENTIALS_MISSING"
        self._mqtt_client = None
        self._seen_record_keys: OrderedDict[str, str] = OrderedDict() # key -> signature
        self._last_seen_timestamps: Dict[str, datetime] = {} # entity_key -> last_seen_dt
        self._last_lap_state: Dict[str, Dict[str, Any]] = {} # entity_key -> lap_data
        self._loop_task: Optional[asyncio.Task] = None

    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns structured operational metrics and connection diagnostics without secrets."""
        now = datetime.now(timezone.utc)
        ingestion_lag_seconds = None
        status = self.connection_status

        has_creds = bool(settings.OPENF1_USERNAME and settings.OPENF1_PASSWORD)

        if not has_creds and (status == "DISCONNECTED" or status == "CREDENTIALS_MISSING"):
            status = "CREDENTIALS_MISSING"

        if self.is_connected:
            if self.last_upstream_timestamp:
                ingestion_lag_seconds = round((now - self.last_upstream_timestamp).total_seconds(), 3)
                if ingestion_lag_seconds <= 30.0:
                    status = "CONNECTED_RECEIVING"
                else:
                    status = "CONNECTED_IDLE"
            else:
                status = "CONNECTED_IDLE"

        return {
            "upstream_provider": "OpenF1_MQTT_Stream",
            "connection_status": status,
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
            "total_out_of_order_filtered": self.total_out_of_order_filtered,
            "has_credentials": has_creds
        }

    async def start_streaming(self, session_key: str):
        """Starts upstream streaming subscription for a specific session."""
        self.active_session_key = str(session_key)
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

    def _parse_iso_datetime(self, date_val: Any) -> Optional[datetime]:
        """Safely parses ISO timestamp strings or numbers into UTC datetime."""
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val.astimezone(timezone.utc)
        if isinstance(date_val, (int, float)):
            try:
                return datetime.fromtimestamp(date_val, tz=timezone.utc)
            except Exception:
                return None
        if isinstance(date_val, str):
            try:
                # Handle 'Z' suffix or standard ISO format
                clean_str = date_val.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                return None
        return None

    def _handle_raw_message(self, topic: str, payload_bytes: bytes):
        """Validates, deduplicates, and processes an incoming MQTT message payload."""
        try:
            now = datetime.now(timezone.utc)
            self.last_upstream_timestamp = now
            self.total_messages_received += 1

            if not payload_bytes:
                return

            try:
                payload = json.loads(payload_bytes.decode("utf-8"))
            except Exception:
                # Malformed JSON payload dropped safely
                return

            if not isinstance(payload, dict):
                return

            # Check if message is for our active session key (reject cross-session data)
            msg_session_key = str(payload.get("session_key", "")).strip()
            if self.active_session_key and msg_session_key and msg_session_key != str(self.active_session_key):
                return # Discard other sessions

            # Identify driver or entity key
            driver_number = payload.get("driver_number")
            entity_id = f"{topic}:{driver_number}" if driver_number is not None else topic

            # Parse event timestamp if available
            event_dt = self._parse_iso_datetime(payload.get("date"))

            # Determine unique record identifier
            record_key = (
                payload.get("_id") or 
                payload.get("_key") or 
                payload.get("id") or 
                None
            )
            if not record_key:
                # Fallback record key
                lap_num = payload.get("lap_number", "")
                date_str = str(payload.get("date", ""))
                record_key = f"{topic}:{driver_number}:{lap_num}:{date_str}"

            # Create a content signature to distinguish exact re-delivery vs incremental update
            # Include keys that change incrementally (lap duration, sectors, position deltas, interval)
            sig_dict = {k: v for k, v in payload.items() if not k.startswith("_")}
            content_sig = json.dumps(sig_dict, sort_keys=True, default=str)

            # Check deduplication cache
            if record_key in self._seen_record_keys:
                existing_sig = self._seen_record_keys[record_key]
                if existing_sig == content_sig:
                    # Identical repeated delivery
                    self.total_duplicates_filtered += 1
                    return
                # If content differs, it's an incremental update sharing the same record identifier!
                # E.g. lap completed sector 2, or interval updated for the same timestamp/lap.
                # Update signature in cache
                self._seen_record_keys[record_key] = content_sig
                self._seen_record_keys.move_to_end(record_key)
            else:
                self._seen_record_keys[record_key] = content_sig
                if len(self._seen_record_keys) > 2000:
                    self._seen_record_keys.popitem(last=False)

            # Event ordering check per entity
            if event_dt is not None:
                last_dt = self._last_seen_timestamps.get(entity_id)
                if last_dt is not None:
                    # If this message has an older timestamp than what we already processed for this entity
                    # and it's not a multi-sector enrichment for the same active lap
                    if event_dt < last_dt:
                        self.total_out_of_order_filtered += 1
                        return
                self._last_seen_timestamps[entity_id] = event_dt

            # Lap sector progression handling: allow incremental sector enrichments
            if topic == "v1/laps" and driver_number is not None:
                lap_num = payload.get("lap_number")
                prev_lap_state = self._last_lap_state.get(entity_id, {})
                if prev_lap_state.get("lap_number") == lap_num:
                    # Merge any previous sectors if new message omitted them
                    for sec_field in ["duration_sector_1", "duration_sector_2", "duration_sector_3"]:
                        if sec_field in prev_lap_state and sec_field not in payload:
                            payload[sec_field] = prev_lap_state[sec_field]
                self._last_lap_state[entity_id] = dict(payload)

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

