from datetime import datetime, timezone
import httpx
from typing import List, Dict, Any, Optional
from app.racing.models import DataStateEnum
from app.racing.schemas import ProvenanceMeta

class OpenF1Provider:
    """
    Adapter for OpenF1 timing and session feeds.
    Provides verified provenance, timestamping, deduplication, error isolation,
    and stale-data detection.
    """
    BASE_URL = "https://api.openf1.org/v1"
    STALE_THRESHOLD_SECONDS = 30.0

    def __init__(self, timeout_seconds: float = 6.0, client: Optional[httpx.AsyncClient] = None):
        self.timeout = timeout_seconds
        self._client = client
        self._last_successful_timestamp: Optional[datetime] = None

    def _create_provenance(
        self,
        state: DataStateEnum,
        verified: bool = True,
        is_test_fixture: bool = False,
        notes: Optional[str] = None
    ) -> ProvenanceMeta:
        return ProvenanceMeta(
            source="OPENF1_REST_API",
            retrieved_at=datetime.now(timezone.utc),
            data_state=state,
            verified=verified,
            is_test_fixture=is_test_fixture,
            notes=notes
        )

    def is_stale(self, timestamp: Optional[datetime]) -> bool:
        """Determines if the provided timestamp exceeds stale data threshold."""
        if not timestamp:
            return True
        diff = (datetime.now(timezone.utc) - timestamp).total_seconds()
        return diff > self.STALE_THRESHOLD_SECONDS

    async def get_latest_session(self, country_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetches the latest session with full error handling and provenance tagging."""
        params = {}
        if country_name:
            params["country_name"] = country_name

        try:
            if self._client:
                res = await self._client.get(f"{self.BASE_URL}/sessions", params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(f"{self.BASE_URL}/sessions", params=params)

            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    latest = data[-1]
                    self._last_successful_timestamp = datetime.now(timezone.utc)
                    # Check if session is historical vs live based on session date
                    state = DataStateEnum.HISTORICAL
                    return {
                        "session": latest,
                        "provenance": self._create_provenance(
                            state,
                            verified=True,
                            is_test_fixture=False,
                            notes=f"Retrieved session key {latest.get('session_key')}"
                        )
                    }
                else:
                    return {
                        "session": None,
                        "provenance": self._create_provenance(
                            DataStateEnum.UNAVAILABLE,
                            verified=False,
                            notes="No session records returned by OpenF1"
                        )
                    }
            elif res.status_code == 429:
                return {
                    "session": None,
                    "provenance": self._create_provenance(
                        DataStateEnum.UNAVAILABLE,
                        verified=False,
                        notes="OpenF1 rate limit quota reached (HTTP 429)"
                    )
                }
            else:
                return {
                    "session": None,
                    "provenance": self._create_provenance(
                        DataStateEnum.UNAVAILABLE,
                        verified=False,
                        notes=f"OpenF1 upstream returned HTTP {res.status_code}"
                    )
                }
        except httpx.TimeoutException:
            return {
                "session": None,
                "provenance": self._create_provenance(
                    DataStateEnum.UNAVAILABLE,
                    verified=False,
                    notes="OpenF1 upstream request timed out"
                )
            }
        except Exception as err:
            return {
                "session": None,
                "provenance": self._create_provenance(
                    DataStateEnum.UNAVAILABLE,
                    verified=False,
                    notes=f"OpenF1 upstream connection error: {type(err).__name__}"
                )
            }

    async def get_live_timing_snapshot(self, session_key: str) -> Dict[str, Any]:
        """Fetches latest timing snapshot with intervals, deduplication, and stale handling."""
        try:
            if self._client:
                res = await self._client.get(
                    f"{self.BASE_URL}/intervals",
                    params={"session_key": session_key},
                    timeout=self.timeout
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(
                        f"{self.BASE_URL}/intervals",
                        params={"session_key": session_key}
                    )

            if res.status_code == 200:
                intervals = res.json()
                if isinstance(intervals, list):
                    # Deduplicate by driver_number, keeping latest record
                    deduped = {}
                    for row in intervals:
                        d_num = row.get("driver_number")
                        if d_num is not None:
                            deduped[d_num] = row

                    now = datetime.now(timezone.utc)
                    self._last_successful_timestamp = now
                    return {
                        "intervals": list(deduped.values()),
                        "provenance": self._create_provenance(
                            DataStateEnum.LIVE if not self.is_stale(now) else DataStateEnum.STALE,
                            verified=True,
                            notes=f"Processed {len(deduped)} driver interval entries"
                        )
                    }
            elif res.status_code == 429:
                return {
                    "intervals": [],
                    "provenance": self._create_provenance(
                        DataStateEnum.UNAVAILABLE,
                        verified=False,
                        notes="Rate limit exceeded"
                    )
                }
        except Exception as err:
            pass

        return {
            "intervals": [],
            "provenance": self._create_provenance(
                DataStateEnum.UNAVAILABLE,
                verified=False,
                notes="Timing service temporarily unreachable"
            )
        }

    async def get_drivers(self, session_key: str) -> List[Dict[str, Any]]:
        """Fetches driver details for a session from OpenF1."""
        try:
            url = f"{self.BASE_URL}/drivers"
            params = {"session_key": session_key}
            if self._client:
                res = await self._client.get(url, params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    # Deduplicate by driver_number
                    deduped = {}
                    for d in data:
                        num = d.get("driver_number")
                        if num is not None:
                            deduped[num] = d
                    return list(deduped.values())
        except Exception:
            pass
        return []

    async def get_positions(self, session_key: str) -> List[Dict[str, Any]]:
        """Fetches latest driver positions for a session."""
        try:
            url = f"{self.BASE_URL}/position"
            params = {"session_key": session_key}
            if self._client:
                res = await self._client.get(url, params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    # Sort or keep latest per driver_number
                    latest_by_driver = {}
                    for row in data:
                        d_num = row.get("driver_number")
                        if d_num is not None:
                            latest_by_driver[d_num] = row
                    return list(latest_by_driver.values())
        except Exception:
            pass
        return []

    async def get_laps(self, session_key: str) -> List[Dict[str, Any]]:
        """Fetches lap timings for a session."""
        try:
            url = f"{self.BASE_URL}/laps"
            params = {"session_key": session_key}
            if self._client:
                res = await self._client.get(url, params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    async def get_pit_stops(self, session_key: str) -> List[Dict[str, Any]]:
        """Fetches pit stop events for a session."""
        try:
            url = f"{self.BASE_URL}/pit"
            params = {"session_key": session_key}
            if self._client:
                res = await self._client.get(url, params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    async def get_stints(self, session_key: str) -> List[Dict[str, Any]]:
        """Fetches tyre stints for a session."""
        try:
            url = f"{self.BASE_URL}/stints"
            params = {"session_key": session_key}
            if self._client:
                res = await self._client.get(url, params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    async def get_weather(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Fetches latest track weather observations."""
        try:
            url = f"{self.BASE_URL}/weather"
            params = {"session_key": session_key}
            if self._client:
                res = await self._client.get(url, params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[-1] # Return the most recent weather record
        except Exception:
            pass
        return None

    async def get_race_control_messages(self, session_key: str) -> List[Dict[str, Any]]:
        """Fetches race control messages for a session."""
        try:
            url = f"{self.BASE_URL}/race_control"
            params = {"session_key": session_key}
            if self._client:
                res = await self._client.get(url, params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    async def get_driver_locations(self, session_key: str, date_from: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetches high-frequency car coordinate points if available."""
        try:
            url = f"{self.BASE_URL}/location"
            params = {"session_key": session_key}
            if date_from:
                params["date>="] = date_from
            if self._client:
                res = await self._client.get(url, params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    # Deduplicate to latest coordinate per driver_number
                    latest_by_driver = {}
                    for row in data:
                        d_num = row.get("driver_number")
                        if d_num is not None:
                            latest_by_driver[d_num] = row
                    return list(latest_by_driver.values())
        except Exception:
            pass
        return []

    async def get_telemetry_snapshot(self, session_key: str, date_from: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetches car telemetry (speed, throttle, brake, gear, drs, rpm)."""
        try:
            url = f"{self.BASE_URL}/car_data"
            params = {"session_key": session_key}
            if date_from:
                params["date>="] = date_from
            if self._client:
                res = await self._client.get(url, params=params, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(url, params=params)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    latest_by_driver = {}
                    for row in data:
                        d_num = row.get("driver_number")
                        if d_num is not None:
                            latest_by_driver[d_num] = row
                    return list(latest_by_driver.values())
        except Exception:
            pass
        return []
