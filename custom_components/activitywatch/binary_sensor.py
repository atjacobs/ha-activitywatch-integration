"""Binary sensor platform for ActivityWatch."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_DEVICE_NAME, CONF_MONITORED_CATEGORIES, DOMAIN
from .coordinator import ActivityWatchCoordinator, ActivityWatchData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ActivityWatch binary sensors from a config entry."""
    coordinator: ActivityWatchCoordinator = entry.runtime_data

    entities: list[BinarySensorEntity] = [
        ActivityWatchActiveBinarySensor(coordinator, entry)
    ]

    categories = entry.options.get(CONF_MONITORED_CATEGORIES, [])
    for category in categories:
        entities.append(ActivityWatchCategoryBinarySensor(coordinator, entry, category))

    async_add_entities(entities)


class ActivityWatchActiveBinarySensor(
    CoordinatorEntity[ActivityWatchCoordinator], BinarySensorEntity
):
    """Binary sensor indicating whether user is active (not AFK)."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PRESENCE

    def __init__(
        self,
        coordinator: ActivityWatchCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        device_name = entry.data[CONF_DEVICE_NAME]
        self._attr_unique_id = f"{entry.entry_id}_active"
        self._attr_name = f"{device_name} Active"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="ActivityWatch",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if user is active (not AFK)."""
        data: ActivityWatchData = self.coordinator.data
        if data is None or data.afk_event is None:
            return None
        status = data.afk_event.get("data", {}).get("status", "")
        return status == "not-afk"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes."""
        data: ActivityWatchData = self.coordinator.data
        if data is None or data.afk_event is None:
            return None
        return {
            "last_active": data.afk_event.get("timestamp", ""),
        }


class ActivityWatchCategoryBinarySensor(
    CoordinatorEntity[ActivityWatchCoordinator], BinarySensorEntity
):
    """Binary sensor that turns ON when current activity matches a category."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ActivityWatchCoordinator,
        entry: ConfigEntry,
        category: str,
    ) -> None:
        """Initialize the category binary sensor."""
        super().__init__(coordinator)
        device_name = entry.data[CONF_DEVICE_NAME]
        self._category = category
        cat_slug = slugify(category)
        self._attr_unique_id = f"{entry.entry_id}_is_{cat_slug}"
        self._attr_name = f"{device_name} Is {category}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="ActivityWatch",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if current activity matches this category."""
        data: ActivityWatchData = self.coordinator.data
        if data is None or data.window_event is None:
            return None
        event_data = data.window_event.get("data", {})
        category_list = event_data.get("$category", [])
        if isinstance(category_list, list):
            return self._category.lower() in [c.lower() for c in category_list]
        return False
