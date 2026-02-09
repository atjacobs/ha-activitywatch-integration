"""Sensor platform for ActivityWatch."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_NAME, DOMAIN
from .coordinator import ActivityWatchCoordinator, ActivityWatchData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ActivityWatch sensors from a config entry."""
    coordinator: ActivityWatchCoordinator = entry.runtime_data
    async_add_entities([ActivityWatchCurrentActivitySensor(coordinator, entry)])


class ActivityWatchCurrentActivitySensor(
    CoordinatorEntity[ActivityWatchCoordinator], SensorEntity
):
    """Sensor showing current activity category."""

    _attr_has_entity_name = True
    _attr_translation_key = "current_activity"

    def __init__(
        self,
        coordinator: ActivityWatchCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        device_name = entry.data[CONF_DEVICE_NAME]
        self._attr_unique_id = f"{entry.entry_id}_current_activity"
        self._attr_name = f"{device_name} Current Activity"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="ActivityWatch",
        )

    @property
    def native_value(self) -> str | None:
        """Return the top-level category or Uncategorized."""
        data: ActivityWatchData = self.coordinator.data
        if data is None or data.window_event is None:
            return None
        event_data = data.window_event.get("data", {})
        category = event_data.get("$category")
        if category and isinstance(category, list) and len(category) > 0:
            return str(category[0])
        return "Uncategorized"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        data: ActivityWatchData = self.coordinator.data
        if data is None or data.window_event is None:
            return None
        event_data = data.window_event.get("data", {})
        category = event_data.get("$category", [])
        return {
            "app_name": event_data.get("app", ""),
            "window_title": event_data.get("title", ""),
            "url": event_data.get("url", ""),
            "sub_categories": category if isinstance(category, list) else [],
            "duration": int(data.window_event.get("duration", 0)),
        }
