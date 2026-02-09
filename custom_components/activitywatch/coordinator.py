"""DataUpdateCoordinator for ActivityWatch."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ActivityWatchApiClient,
    ActivityWatchApiConnectionError,
    ActivityWatchApiError,
)
from .const import (
    BUCKET_AFK,
    BUCKET_WINDOW,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_ACTIVITY_SWITCH,
)

_LOGGER = logging.getLogger(__name__)


class ActivityWatchData:
    """Container for ActivityWatch coordinator data."""

    def __init__(self) -> None:
        """Initialize data container."""
        self.window_event: dict[str, Any] | None = None
        self.afk_event: dict[str, Any] | None = None


class ActivityWatchCoordinator(DataUpdateCoordinator[ActivityWatchData]):
    """Coordinator that polls ActivityWatch for window and AFK events."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ActivityWatchApiClient,
        device_name: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.device_name = device_name
        self.window_bucket: str | None = None
        self.afk_bucket: str | None = None
        self._previous_window_app: str | None = None

    async def async_setup(self) -> None:
        """Discover AW buckets."""
        window_buckets = await self.client.async_find_buckets(BUCKET_WINDOW)
        if window_buckets:
            self.window_bucket = window_buckets[0]
            _LOGGER.debug("Found window bucket: %s", self.window_bucket)

        afk_buckets = await self.client.async_find_buckets(BUCKET_AFK)
        if afk_buckets:
            self.afk_bucket = afk_buckets[0]
            _LOGGER.debug("Found AFK bucket: %s", self.afk_bucket)

    async def _async_update_data(self) -> ActivityWatchData:
        """Fetch data from ActivityWatch."""
        data = ActivityWatchData()

        try:
            if self.window_bucket:
                events = await self.client.async_get_events(self.window_bucket, limit=1)
                if events:
                    data.window_event = events[0]

            if self.afk_bucket:
                events = await self.client.async_get_events(self.afk_bucket, limit=1)
                if events:
                    data.afk_event = events[0]

        except ActivityWatchApiConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except ActivityWatchApiError as err:
            raise UpdateFailed(f"API error: {err}") from err

        self._fire_window_switch_event(data)

        return data

    def _fire_window_switch_event(self, data: ActivityWatchData) -> None:
        """Fire an event on the HA event bus when the active window changes."""
        if data.window_event is None:
            return

        event_data = data.window_event.get("data", {})
        current_app = event_data.get("app")

        if self._previous_window_app is None:
            # First poll — record but don't fire
            self._previous_window_app = current_app
            return

        if current_app != self._previous_window_app:
            self._previous_window_app = current_app
            self.hass.bus.async_fire(
                EVENT_ACTIVITY_SWITCH,
                {
                    "device_id": self.device_name,
                    "type": "window_switch",
                    "app": current_app,
                    "title": event_data.get("title", ""),
                    "url": event_data.get("url", ""),
                },
            )
